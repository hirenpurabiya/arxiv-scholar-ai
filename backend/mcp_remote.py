"""
ArXiv Scholar AI - Remote MCP Server (SSE Transport)

Same tools/resources/prompts as the stdio server, but exposed over
HTTP using Server-Sent Events (SSE). Deploy this on Render, Railway,
or any cloud provider.

Run locally:  python mcp_remote.py
Default port: 8001 (or set MCP_PORT env var)
"""

import logging
import os

from mcp.server.fastmcp import FastMCP

from src.article_finder import find_articles
from src.article_reader import get_article_details, list_all_topics, get_articles_by_topic
from src.summarizer import summarize_article, explain_like_ten as eli10
from src.chat_engine import chat_about_article

import json
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("arxiv-scholar-ai-remote")


# --------------- Tools (same as stdio server) ---------------

@mcp.tool()
def search_arxiv(
    topic: str,
    max_results: int = 5,
    sort_by: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> str:
    """Search arXiv for academic papers on a given topic."""
    max_results = max(1, min(20, max_results))
    articles = find_articles(
        topic=topic,
        max_results=max_results,
        sort_by=sort_by,
        date_from=date_from,
        date_to=date_to,
    )
    if not articles:
        return json.dumps({"count": 0, "message": f"No papers found for '{topic}'."})

    results = [{
        "id": a["id"],
        "title": a["title"],
        "authors": a["authors"],
        "published": a["published"],
        "pdf_url": a["pdf_url"],
    } for a in articles]

    return json.dumps({"count": len(results), "papers": results}, indent=2)


@mcp.tool()
def get_paper(article_id: str) -> str:
    """Get full metadata for a specific arXiv paper by its ID."""
    article = get_article_details(article_id)
    if not article:
        return json.dumps({"error": f"Paper '{article_id}' not found."})
    return json.dumps(article, indent=2)


@mcp.tool()
def summarize_paper(article_id: str) -> str:
    """Generate an AI-powered summary of a paper."""
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found."
    return summarize_article(article) or "Could not generate summary."


@mcp.tool()
def explain_paper(article_id: str) -> str:
    """Explain a paper in simple terms a 10-year-old could understand."""
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found."
    return eli10(article) or "Could not generate explanation."


@mcp.tool()
def chat_about_paper(article_id: str, message: str) -> str:
    """Have an interactive conversation about a paper."""
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found."
    result = chat_about_article(article, message, history=[], provider="gemini")
    return result.get("response", "Could not get a response.")


# --------------- Resources ---------------

@mcp.resource("arxiv://topics")
def get_topics_resource() -> str:
    """List all saved research topics."""
    topics = list_all_topics()
    if not topics:
        return "No topics saved yet."
    lines = [f"- {t.replace('_', ' ').title()}" for t in topics]
    return f"# Saved Topics ({len(topics)})\n\n" + "\n".join(lines)


@mcp.resource("arxiv://topic/{slug}")
def get_topic_resource(slug: str) -> str:
    """Get all saved papers for a topic."""
    articles = get_articles_by_topic(slug)
    if not articles:
        return f"No papers for '{slug}'."
    lines = [f"# {slug.replace('_', ' ').title()} ({len(articles)} papers)\n"]
    for pid, p in articles.items():
        lines.append(f"- [{p.get('title', pid)}]({p.get('pdf_url', '')})")
    return "\n".join(lines)


@mcp.resource("arxiv://paper/{article_id}")
def get_paper_resource(article_id: str) -> str:
    """Get detailed metadata for a specific paper."""
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found."
    return json.dumps(article, indent=2)


# --------------- Prompts ---------------

@mcp.prompt()
def research_summary(topic: str, num_papers: int = 5) -> str:
    """Search and summarize papers on a topic."""
    return (
        f"Search for {num_papers} papers about '{topic}' using search_arxiv. "
        f"Summarize each with summarize_paper, then give an overview of themes, "
        f"findings, and gaps."
    )


@mcp.prompt()
def explain_like_ten(topic: str) -> str:
    """Search for papers and explain them simply."""
    return (
        f"Find papers about '{topic}' using search_arxiv, pick the most relevant, and explain it "
        f"simply using explain_paper. Add everyday examples."
    )


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8001"))
    logger.info(f"Starting SSE server on port {port}")
    mcp.run(transport="sse", port=port)
