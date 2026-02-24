"""
MCP Agent for ArXiv Scholar AI.

Connects to the MCP server as a real SSE client, discovers tools dynamically,
and runs an agentic loop: Gemini decides which MCP tools to call,
the agent executes them via the MCP protocol, and yields reasoning steps
for real-time streaming to the frontend.
"""

import json
import logging
import re
import time
from typing import AsyncGenerator, Dict, Any

import requests
from mcp import ClientSession
from mcp.client.sse import sse_client

from .config import GOOGLE_API_KEY, MCP_SERVER_URL

logger = logging.getLogger(__name__)

AGENT_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_TOOL_RESULT_CHARS = 3000


def _sanitize_error(msg: str) -> str:
    """Strip API keys and URLs from error messages before sending to the client."""
    msg = re.sub(r'key=[A-Za-z0-9_-]+', 'key=***', msg)
    msg = re.sub(r'https?://\S+', '[API endpoint]', msg)
    return msg


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


def _call_gemini(messages: list, tools: list) -> dict:
    """
    Call Gemini API with function declarations.

    Tries each model in AGENT_MODELS (flash-lite first, then flash).
    Each model has its own rate limit quota, so if one is 429'd the
    other may still work. Runs up to 3 rounds with increasing waits
    between rounds (0s, 10s, 20s). Both models are Gemini 2.0 with
    identical API formats, so they're safe to interchange mid-conversation.
    """
    payload: dict = {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are ArXiv Scholar AI, a research assistant that helps users "
                    "explore academic papers from arXiv. You MUST use the available tools "
                    "to answer every question. Always call search_arxiv first to find papers. "
                    "Never answer from memory alone — search first, then summarize or explain."
                )
            }]
        },
        "contents": messages,
        "tools": [{"functionDeclarations": tools}],
    }
    payload_size = len(json.dumps(payload))
    logger.info(f"Gemini payload: {payload_size} chars")

    last_error = None
    max_rounds = 3
    round_waits = [0, 10, 20]

    for round_num in range(max_rounds):
        if round_waits[round_num] > 0:
            logger.info(f"All models 429'd, waiting {round_waits[round_num]}s before round {round_num + 1}")
            time.sleep(round_waits[round_num])

        for model in AGENT_MODELS:
            url = f"{API_BASE}/{model}:generateContent?key={GOOGLE_API_KEY}"
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 429:
                    reason = resp.text[:200]
                    logger.warning(f"429 on {model} (round {round_num + 1}): {reason}")
                    last_error = f"Rate limited on {model}"
                    continue
                if resp.status_code != 200:
                    body = resp.text[:300]
                    logger.warning(f"{model} returned {resp.status_code}: {body}")
                    last_error = f"{model} returned {resp.status_code}"
                    continue
                logger.info(f"Gemini OK on {model} (round {round_num + 1}), ~{len(resp.text)} chars")
                return resp.json()
            except requests.exceptions.Timeout:
                last_error = f"Timeout calling {model}"
                logger.warning(last_error)
                continue
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error calling {model}: {e}")
                continue

    sanitized = _sanitize_error(last_error or "Unknown error")
    raise RuntimeError(
        f"Gemini is busy ({sanitized}). Please wait about 60 seconds and try again."
    )


def _extract_text(response: dict) -> str | None:
    """Pull text from a Gemini response."""
    try:
        for part in response["candidates"][0]["content"]["parts"]:
            if "text" in part:
                return part["text"]
    except (KeyError, IndexError):
        pass
    return None


def _extract_tool_calls(response: dict) -> list:
    """Pull function-call requests from a Gemini response."""
    calls = []
    try:
        for part in response["candidates"][0]["content"]["parts"]:
            if "functionCall" in part:
                calls.append(part["functionCall"])
    except (KeyError, IndexError):
        pass
    return calls


async def run_mcp_agent(query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Run the MCP agentic loop for a user query.

    Connects to the MCP server via SSE, discovers tools dynamically,
    and executes them through the MCP protocol. Yields reasoning step
    dicts for SSE streaming to the frontend.

    Each step: {"type": "thinking"|"tool_call"|"tool_result"|"answer"|"error", "content": ...}
    """
    if not GOOGLE_API_KEY:
        yield {"type": "error", "content": "Google API key not configured."}
        return

    yield {"type": "thinking", "content": "Connecting to MCP server..."}

    try:
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # Discover tools dynamically from the MCP server
                tools_result = await session.list_tools()
                mcp_tools = tools_result.tools
                gemini_declarations = _mcp_tools_to_gemini(mcp_tools)

                tool_names = [t.name for t in mcp_tools]
                yield {
                    "type": "thinking",
                    "content": f"Connected to MCP server. Discovered {len(mcp_tools)} tools: {', '.join(tool_names)}. Understanding your query...",
                }

                conversation = [{"role": "user", "parts": [{"text": query}]}]

                try:
                    response = _call_gemini(conversation, gemini_declarations)
                except Exception as e:
                    logger.error(f"Gemini initial call failed: {e}")
                    yield {"type": "error", "content": _sanitize_error(str(e))}
                    return

                tool_calls = _extract_tool_calls(response)
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

                        # Truncate for Gemini conversation (save tokens, avoid timeouts)
                        gemini_result = full_result
                        if len(gemini_result) > MAX_TOOL_RESULT_CHARS:
                            gemini_result = gemini_result[:MAX_TOOL_RESULT_CHARS] + "\n...[truncated]"

                        function_responses.append({
                            "functionResponse": {
                                "name": fn_name,
                                "response": {"result": gemini_result},
                            }
                        })

                    conversation.append({"role": "function", "parts": function_responses})

                    try:
                        response = _call_gemini(conversation, gemini_declarations)
                    except Exception as e:
                        logger.error(f"Gemini follow-up call failed: {e}")
                        yield {"type": "error", "content": _sanitize_error(str(e))}
                        return

                    tool_calls = _extract_tool_calls(response)

                answer = _extract_text(response)
                if answer:
                    logger.info(f"Agent complete: {iteration} iterations, answer={len(answer)} chars")
                    yield {"type": "answer", "content": answer}
                else:
                    logger.warning("Agent complete but no text in final Gemini response")
                    yield {"type": "error", "content": "No response from AI."}

                yield {"type": "done", "content": ""}

    except Exception as e:
        logger.error(f"MCP connection failed: {e}")
        yield {"type": "error", "content": f"Could not connect to MCP server: {_sanitize_error(str(e))}"}
