"""
MCP Agent for ArXiv Scholar AI.
Runs an agentic loop: sends user queries to Gemini with MCP tool declarations,
executes tool calls, and yields reasoning steps for real-time streaming.
"""

import json
import logging
from typing import Generator, Dict, Any

import requests

from .config import GOOGLE_API_KEY
from .article_finder import find_articles
from .article_reader import get_article_details
from .summarizer import summarize_article, explain_like_ten
from .chat_engine import chat_about_article

logger = logging.getLogger(__name__)

AGENT_MODEL = "gemini-2.0-flash"
AGENT_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{AGENT_MODEL}"
    f":generateContent"
)

TOOL_DECLARATIONS = [
    {
        "name": "search_arxiv",
        "description": (
            "Search arXiv for academic papers on a given topic. "
            "Returns paper IDs, titles, authors, and publication dates."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "topic": {
                    "type": "STRING",
                    "description": "Research topic to search for (e.g. 'transformer architecture')",
                },
                "max_results": {
                    "type": "INTEGER",
                    "description": "Number of papers to return (1-20, default 5)",
                },
                "sort_by": {
                    "type": "STRING",
                    "description": "Sort order: 'relevance', 'date', or 'updated'",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "get_paper",
        "description": "Get full metadata for a specific arXiv paper by its ID.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "article_id": {
                    "type": "STRING",
                    "description": "The arXiv short ID (e.g. '2401.12345v2')",
                },
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "summarize_paper",
        "description": "Generate a concise AI-powered summary of a paper's abstract.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "article_id": {
                    "type": "STRING",
                    "description": "The arXiv short ID of the paper to summarize",
                },
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "explain_paper",
        "description": "Explain a paper in simple terms a 10-year-old could understand.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "article_id": {
                    "type": "STRING",
                    "description": "The arXiv short ID of the paper to explain",
                },
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "chat_about_paper",
        "description": "Ask a question about a specific paper and get a simple answer.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "article_id": {
                    "type": "STRING",
                    "description": "The arXiv short ID of the paper",
                },
                "message": {
                    "type": "STRING",
                    "description": "The question to ask about the paper",
                },
            },
            "required": ["article_id", "message"],
        },
    },
]


def _call_gemini(messages: list, tools: list) -> dict:
    """Call Gemini API with function declarations and return parsed response."""
    payload: dict = {
        "contents": messages,
        "tools": [{"functionDeclarations": tools}],
    }
    resp = requests.post(
        f"{AGENT_API_URL}?key={GOOGLE_API_KEY}",
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


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


def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool by name, calling the underlying backend functions directly."""
    if name == "search_arxiv":
        articles = find_articles(
            topic=args["topic"],
            max_results=min(20, max(1, int(args.get("max_results", 5)))),
            sort_by=args.get("sort_by", "relevance"),
        )
        if not articles:
            return json.dumps({"count": 0, "message": f"No papers found for '{args['topic']}'."})
        results = [
            {"id": a["id"], "title": a["title"], "authors": a["authors"][:3], "published": a["published"]}
            for a in articles
        ]
        return json.dumps({"count": len(results), "papers": results}, indent=2)

    if name == "get_paper":
        article = get_article_details(args["article_id"])
        if not article:
            return json.dumps({"error": f"Paper '{args['article_id']}' not found. Try searching first."})
        return json.dumps(article, indent=2)

    if name == "summarize_paper":
        article = get_article_details(args["article_id"])
        if not article:
            return f"Paper '{args['article_id']}' not found."
        return summarize_article(article) or "Could not generate summary."

    if name == "explain_paper":
        article = get_article_details(args["article_id"])
        if not article:
            return f"Paper '{args['article_id']}' not found."
        return explain_like_ten(article) or "Could not generate explanation."

    if name == "chat_about_paper":
        article = get_article_details(args["article_id"])
        if not article:
            return f"Paper '{args['article_id']}' not found."
        result = chat_about_article(article, args["message"], history=[], provider="gemini")
        return result.get("response", "Could not get a response.")

    return f"Unknown tool: {name}"


def _truncate(text: str, limit: int = 500) -> str:
    """Truncate long text for the streaming display."""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def run_mcp_agent(query: str) -> Generator[Dict[str, Any], None, None]:
    """
    Run the MCP agentic loop for a user query.
    Yields reasoning step dicts for SSE streaming to the frontend.
    Each step: {"type": "thinking"|"tool_call"|"tool_result"|"answer"|"error", "content": ...}
    """
    if not GOOGLE_API_KEY:
        yield {"type": "error", "content": "Google API key not configured."}
        return

    yield {"type": "thinking", "content": "Understanding your query..."}

    conversation = [{"role": "user", "parts": [{"text": query}]}]

    try:
        response = _call_gemini(conversation, TOOL_DECLARATIONS)
    except Exception as e:
        logger.error(f"Gemini initial call failed: {e}")
        yield {"type": "error", "content": f"AI service error: {e}"}
        return

    tool_calls = _extract_tool_calls(response)
    max_iterations = 10
    iteration = 0

    while tool_calls and iteration < max_iterations:
        iteration += 1
        conversation.append(response["candidates"][0]["content"])

        function_responses = []
        for fc in tool_calls:
            fn_name = fc["name"]
            fn_args = fc.get("args", {})

            yield {"type": "tool_call", "content": {"name": fn_name, "args": fn_args}}

            try:
                result_text = _execute_tool(fn_name, fn_args)
            except Exception as e:
                logger.error(f"Tool {fn_name} error: {e}")
                result_text = f"Error executing {fn_name}: {e}"

            yield {
                "type": "tool_result",
                "content": {"name": fn_name, "result": _truncate(result_text)},
            }

            function_responses.append({
                "functionResponse": {
                    "name": fn_name,
                    "response": {"result": result_text},
                }
            })

        conversation.append({"role": "function", "parts": function_responses})

        try:
            response = _call_gemini(conversation, TOOL_DECLARATIONS)
        except Exception as e:
            logger.error(f"Gemini follow-up call failed: {e}")
            yield {"type": "error", "content": f"AI service error: {e}"}
            return

        tool_calls = _extract_tool_calls(response)

    answer = _extract_text(response)
    if answer:
        yield {"type": "answer", "content": answer}
    else:
        yield {"type": "error", "content": "No response from AI."}

    yield {"type": "done", "content": ""}
