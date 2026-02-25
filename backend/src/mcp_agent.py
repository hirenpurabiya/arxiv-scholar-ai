"""
MCP Agent for ArXiv Scholar AI.

Connects to the MCP server as a real SSE client, discovers tools dynamically,
and runs an agentic loop: the LLM decides which MCP tools to call,
the agent executes them via the MCP protocol, and yields reasoning steps
for real-time streaming to the frontend.

LLM provider strategy (multi-provider, LLM-agnostic):
  1. Google Gemini free tier — tries gemini-2.0-flash-lite, then gemini-2.0-flash
  2. OpenAI GPT-4o-mini — automatic fallback when all Gemini models are rate-limited
"""

import json
import logging
import re
import time
from typing import AsyncGenerator, Dict, Any

import requests
from mcp import ClientSession
from mcp.client.sse import sse_client

from .config import GOOGLE_API_KEY, OPENAI_API_KEY, MCP_SERVER_URL

logger = logging.getLogger(__name__)

# Gemini models to try (flash-lite has higher free RPM, flash is fallback)
GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# OpenAI fallback (only used when ALL Gemini models are rate-limited)
# OpenAI model used as fallback (fast + cheap)
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

MAX_TOOL_RESULT_CHARS = 3000

SYSTEM_PROMPT = (
    "You are ArXiv Scholar AI, a research assistant that helps users "
    "explore academic papers from arXiv.\n\n"
    "CRITICAL RULES:\n"
    "1. You MUST call search_arxiv on EVERY user query. No exceptions.\n"
    "2. NEVER respond with text alone. Always call a tool first.\n"
    "3. If the user query is an abbreviation or acronym (e.g. 'mcp', 'rag', 'llm'), "
    "expand it to its full term before searching (e.g. 'Model Context Protocol', "
    "'Retrieval Augmented Generation', 'Large Language Model').\n"
    "4. If the first search returns no results, try alternative phrasings or related terms.\n"
    "5. Never say 'no papers found' without having called search_arxiv at least once.\n"
    "6. After finding papers, summarize or explain them based on the user's query."
)


def _sanitize_error(msg: str) -> str:
    """Strip API keys and URLs from error messages before sending to the client."""
    msg = re.sub(r'key=[A-Za-z0-9_-]+', 'key=***', msg)
    msg = re.sub(r'https?://\S+', '[API endpoint]', msg)
    return msg


# --------------- Tool Schema Converters ---------------


def _mcp_tools_to_gemini(mcp_tools: list) -> list:
    """Convert MCP tool schemas to Gemini function declarations."""
    type_map = {
        "STRING": "STRING",
        "INTEGER": "INTEGER",
        "NUMBER": "NUMBER",
        "BOOLEAN": "BOOLEAN",
        "ARRAY": "ARRAY",
        "OBJECT": "OBJECT",
    }
    declarations = []
    for tool in mcp_tools:
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        gemini_props = {}
        for name, prop in properties.items():
            prop_type = prop.get("type", "string").upper()
            gemini_props[name] = {
                "type": type_map.get(prop_type, "STRING"),
                "description": prop.get("description", ""),
            }

        declarations.append({
            "name": tool.name,
            "description": tool.description or "",
            "parameters": {
                "type": "OBJECT",
                "properties": gemini_props,
                "required": required,
            },
        })
    return declarations


def _mcp_tools_to_openai(mcp_tools: list) -> list:
    """Convert MCP tool schemas to OpenAI function tool format."""
    tools = []
    for tool in mcp_tools:
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        openai_props = {}
        for name, prop in properties.items():
            openai_props[name] = {
                "type": prop.get("type", "string"),
                "description": prop.get("description", ""),
            }

        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": openai_props,
                    "required": required,
                },
            },
        })
    return tools


# --------------- Message Format Converters ---------------


def _gemini_to_openai_messages(gemini_messages: list) -> list:
    """
    Convert Gemini conversation to OpenAI messages.

    Gemini uses: contents[] with role+parts (functionCall, functionResponse)
    OpenAI uses: messages[] with role (assistant+tool_calls, tool+tool_call_id)
    """
    openai_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    call_counter = 0
    pending_call_ids = []

    for msg in gemini_messages:
        role = msg.get("role", "")
        parts = msg.get("parts", [])

        if role == "user":
            text_parts = [p["text"] for p in parts if "text" in p]
            openai_msgs.append({"role": "user", "content": " ".join(text_parts)})

        elif role == "model":
            text_parts = [p["text"] for p in parts if "text" in p]
            func_calls = [p["functionCall"] for p in parts if "functionCall" in p]

            if func_calls:
                pending_call_ids = []
                tool_calls = []
                for fc in func_calls:
                    call_counter += 1
                    call_id = f"call_{call_counter}"
                    pending_call_ids.append(call_id)
                    tool_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": fc["name"],
                            "arguments": json.dumps(fc.get("args", {})),
                        },
                    })
                assistant_msg: dict = {"role": "assistant", "tool_calls": tool_calls}
                if text_parts:
                    assistant_msg["content"] = " ".join(text_parts)
                openai_msgs.append(assistant_msg)
            elif text_parts:
                openai_msgs.append({"role": "assistant", "content": " ".join(text_parts)})

        elif role == "function":
            responses = [p["functionResponse"] for p in parts if "functionResponse" in p]
            for i, fr in enumerate(responses):
                call_id = pending_call_ids[i] if i < len(pending_call_ids) else f"call_{call_counter + i + 1}"
                result = fr.get("response", {}).get("result", "")
                openai_msgs.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(result),
                })

    return openai_msgs


def _openai_to_gemini_response(openai_data: dict) -> dict:
    """
    Convert OpenAI chat completion response to Gemini response format.

    This lets _extract_text() and _extract_tool_calls() work unchanged,
    regardless of which provider generated the response.
    """
    choice = openai_data["choices"][0]
    message = choice["message"]
    parts = []

    if message.get("content"):
        parts.append({"text": message["content"]})

    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            fn = tc["function"]
            try:
                args = json.loads(fn["arguments"])
            except (json.JSONDecodeError, TypeError):
                args = {}
            parts.append({
                "functionCall": {
                    "name": fn["name"],
                    "args": args,
                }
            })

    return {
        "candidates": [{
            "content": {
                "role": "model",
                "parts": parts,
            }
        }]
    }


# --------------- LLM Call Functions ---------------


def _call_gemini(messages: list, tools: list) -> dict:
    """
    Call Gemini API with function declarations.

    Tries each model in GEMINI_MODELS once (flash-lite first, then flash).
    If both fail (429 or error), raises immediately so OpenAI fallback
    kicks in fast. No retry waits — 429 means "quota exhausted for ~60s"
    so retrying after 10-20s rarely helps and just makes the user wait.
    """
    payload: dict = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": messages,
        "tools": [{"functionDeclarations": tools}],
    }
    payload_size = len(json.dumps(payload))
    logger.info(f"Gemini payload: {payload_size} chars")

    last_error = None

    for model in GEMINI_MODELS:
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={GOOGLE_API_KEY}"
        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 429:
                reason = resp.text[:200]
                logger.warning(f"429 on {model}: {reason}")
                last_error = f"Rate limited on {model}"
                continue
            if resp.status_code != 200:
                body = resp.text[:300]
                logger.warning(f"{model} returned {resp.status_code}: {body}")
                last_error = f"{model} returned {resp.status_code}"
                continue
            logger.info(f"Gemini OK on {model}, ~{len(resp.text)} chars")
            return resp.json()
        except requests.exceptions.Timeout:
            last_error = f"Timeout calling {model}"
            logger.warning(last_error)
            continue
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Error calling {model}: {e}")
            continue

    raise RuntimeError(
        f"All Gemini models exhausted: {_sanitize_error(last_error or 'Unknown error')}"
    )


def _call_openai(gemini_messages: list, openai_tools: list) -> dict:
    """
    Call OpenAI API as fallback. Converts Gemini conversation to OpenAI format,
    makes the call, and converts the response back to Gemini format.

    Returns a Gemini-format response dict so the agentic loop needs no changes.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not configured")

    openai_messages = _gemini_to_openai_messages(gemini_messages)

    payload = {
        "model": OPENAI_MODEL,
        "messages": openai_messages,
        "tools": openai_tools,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.info(f"Falling back to OpenAI {OPENAI_MODEL}")
    try:
        resp = requests.post(OPENAI_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            body = resp.text[:300]
            logger.warning(f"OpenAI {OPENAI_MODEL} returned {resp.status_code}: {body}")
            raise RuntimeError(f"OpenAI returned {resp.status_code}")

        openai_data = resp.json()
        logger.info(f"OpenAI OK on {OPENAI_MODEL}, ~{len(resp.text)} chars")
        return _openai_to_gemini_response(openai_data)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout calling OpenAI {OPENAI_MODEL}")


def _call_llm(gemini_messages: list, gemini_tools: list, openai_tools: list) -> dict:
    """
    Unified LLM call: tries Gemini first (2 models x 3 rounds),
    falls back to OpenAI if all Gemini attempts fail.

    Returns a Gemini-format response dict in all cases.
    """
    gemini_available = bool(GOOGLE_API_KEY)
    openai_available = bool(OPENAI_API_KEY)

    if gemini_available:
        try:
            return _call_gemini(gemini_messages, gemini_tools)
        except RuntimeError as gemini_err:
            if not openai_available:
                sanitized = _sanitize_error(str(gemini_err))
                raise RuntimeError(
                    f"Gemini is busy ({sanitized}). Please wait about 60 seconds and try again."
                )
            logger.warning(f"Gemini failed, trying OpenAI fallback: {gemini_err}")

    if openai_available:
        try:
            return _call_openai(gemini_messages, openai_tools)
        except RuntimeError as openai_err:
            err_str = str(openai_err)
            if "401" in err_str:
                logger.error(f"OpenAI auth failed: {openai_err}")
                raise RuntimeError("OpenAI authentication failed. Check API key permissions.")
            logger.error(f"OpenAI fallback also failed: {openai_err}")
            raise RuntimeError(
                f"AI is busy ({_sanitize_error(err_str)}). Please try again."
            )

    raise RuntimeError("No AI API key configured.")


# --------------- Response Extractors ---------------


def _extract_text(response: dict) -> str | None:
    """Pull text from a Gemini-format response."""
    try:
        for part in response["candidates"][0]["content"]["parts"]:
            if "text" in part:
                return part["text"]
    except (KeyError, IndexError):
        pass
    return None


def _extract_tool_calls(response: dict) -> list:
    """Pull function-call requests from a Gemini-format response."""
    calls = []
    try:
        for part in response["candidates"][0]["content"]["parts"]:
            if "functionCall" in part:
                calls.append(part["functionCall"])
    except (KeyError, IndexError):
        pass
    return calls


# --------------- MCP Agentic Loop ---------------


async def run_mcp_agent(query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the MCP agentic loop for a user query.

    Connects to the MCP server via SSE, discovers tools dynamically,
    and executes them through the MCP protocol. Yields reasoning step
    dicts for SSE streaming to the frontend.

    Each step: {"type": "thinking"|"tool_call"|"tool_result"|"answer"|"error", "content": ...}
    """
    if not GOOGLE_API_KEY and not OPENAI_API_KEY:
        yield {"type": "error", "content": "No AI API key configured."}
        return

    yield {"type": "thinking", "content": "Connecting to MCP server..."}

    try:
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # Discover tools dynamically from the MCP server
                tools_result = await session.list_tools()
                mcp_tools = tools_result.tools
                gemini_tools = _mcp_tools_to_gemini(mcp_tools)
                openai_tools = _mcp_tools_to_openai(mcp_tools)

                tool_names = [t.name for t in mcp_tools]
                yield {
                    "type": "thinking",
                    "content": f"Connected to MCP server. Discovered {len(mcp_tools)} tools: {', '.join(tool_names)}. Understanding your query...",
                }

                conversation = [{"role": "user", "parts": [{"text": query}]}]

                try:
                    response = _call_llm(conversation, gemini_tools, openai_tools)
                except Exception as e:
                    logger.error(f"LLM initial call failed: {e}")
                    yield {"type": "error", "content": _sanitize_error(str(e))}
                    return

                tool_calls = _extract_tool_calls(response)

                # Fallback: if LLM skipped tools, force a search_arxiv call
                if not tool_calls:
                    logger.warning(f"LLM returned no tool calls for query: {query}. Forcing search_arxiv.")
                    yield {"type": "thinking", "content": "Searching arXiv for papers..."}
                    try:
                        forced_result = await session.call_tool("search_arxiv", {"topic": query})
                        forced_text = forced_result.content[0].text if forced_result.content else "No result."
                        yield {"type": "tool_call", "content": {"name": "search_arxiv", "args": {"topic": query}}}
                        yield {"type": "tool_result", "content": {"name": "search_arxiv", "result": forced_text}}

                        # Feed the result back to the LLM for a proper answer
                        llm_result = forced_text
                        if len(llm_result) > MAX_TOOL_RESULT_CHARS:
                            llm_result = llm_result[:MAX_TOOL_RESULT_CHARS] + "\n...[truncated]"
                        conversation.append(response["candidates"][0]["content"])
                        conversation.append({
                            "role": "function",
                            "parts": [{"functionResponse": {"name": "search_arxiv", "response": {"result": llm_result}}}],
                        })
                        response = _call_llm(conversation, gemini_tools, openai_tools)
                        tool_calls = _extract_tool_calls(response)
                    except Exception as e:
                        logger.error(f"Forced search_arxiv failed: {e}")

                max_iterations = 10
                iteration = 0
                rate_limited = False

                while tool_calls and iteration < max_iterations and not rate_limited:
                    iteration += 1
                    conversation.append(response["candidates"][0]["content"])

                    function_responses = []
                    for fc in tool_calls:
                        fn_name = fc["name"]
                        fn_args = fc.get("args", {})

                        yield {"type": "tool_call", "content": {"name": fn_name, "args": fn_args}}

                        try:
                            result = await session.call_tool(fn_name, fn_args)
                            full_result = result.content[0].text if result.content else "No result."
                        except Exception as e:
                            logger.error(f"MCP tool {fn_name} error: {e}")
                            full_result = f"Error executing {fn_name}: {e}"

                        # Stop the loop if arXiv is rate-limiting us
                        if "rate-limiting" in full_result.lower() or "do not retry" in full_result.lower():
                            rate_limited = True

                        # Send FULL result to frontend (so it can parse paper JSON)
                        yield {
                            "type": "tool_result",
                            "content": {"name": fn_name, "result": full_result},
                        }

                        # Truncate for LLM conversation (save tokens, avoid timeouts)
                        llm_result = full_result
                        if len(llm_result) > MAX_TOOL_RESULT_CHARS:
                            llm_result = llm_result[:MAX_TOOL_RESULT_CHARS] + "\n...[truncated]"

                        function_responses.append({
                            "functionResponse": {
                                "name": fn_name,
                                "response": {"result": llm_result},
                            }
                        })

                    conversation.append({"role": "function", "parts": function_responses})

                    try:
                        response = _call_llm(conversation, gemini_tools, openai_tools)
                    except Exception as e:
                        logger.error(f"LLM follow-up call failed: {e}")
                        # Graceful fallback: papers were already sent to frontend
                        # via tool_result, so show a helpful message instead of error
                        yield {
                            "type": "answer",
                            "content": "I found the papers above but couldn't generate a detailed summary right now due to high demand. You can click on any paper to read more, or try again in about 60 seconds for a full AI summary.",
                        }
                        break

                    tool_calls = _extract_tool_calls(response)

                answer = _extract_text(response)
                if answer:
                    logger.info(f"Agent complete: {iteration} iterations, answer={len(answer)} chars")
                    yield {"type": "answer", "content": answer}
                else:
                    logger.warning("Agent complete but no text in final response")
                    yield {"type": "error", "content": "No response from AI."}

                yield {"type": "done", "content": ""}

    except Exception as e:
        logger.error(f"MCP connection failed: {e}")
        yield {"type": "error", "content": f"Could not connect to MCP server: {_sanitize_error(str(e))}"}
