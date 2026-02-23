"""
ArXiv Scholar AI - MCP Server

Exposes arXiv paper search, summarization, and chat as MCP tools,
resources, and prompts. Uses FastMCP and wraps the existing backend
functions directly (no HTTP calls).

Run locally:  python mcp_server.py
Run with MCP inspector:  npx @modelcontextprotocol/inspector python mcp_server.py
"""

import json
import logging
from mcp.server.fastmcp import FastMCP

from src.article_finder import find_articles
from src.article_reader import get_article_details, list_all_topics, get_articles_by_topic
from src.summarizer import summarize_article, explain_like_ten as eli10
from src.chat_engine import chat_about_article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("arxiv-scholar-ai")


# --------------- MCP Tools ---------------

@mcp.tool()
def search_arxiv(
    topic: str,
    max_results: int = 5,
    sort_by: str = "relevance",
) -> str:
    """
    Search arXiv for academic papers on a given topic.

    Args:
        topic: Research topic to search for (e.g. "transformer architecture")
        max_results: Number of papers to return (1-20, default 5)
        sort_by: Sort order - "relevance", "date", or "updated"

    Returns:
        JSON string with list of papers found
    """
    max_results = max(1, min(20, max_results))
    try:
        articles = find_articles(
            topic=topic,
            max_results=max_results,
            sort_by=sort_by,
        )
    except Exception as e:
        if "429" in str(e):
            return json.dumps({
                "count": 0,
                "message": f"arXiv is temporarily rate-limiting requests. The search results for '{topic}' are not available right now. Do NOT retry this tool -- instead, tell the user to try again in about 60 seconds.",
            })
        raise

    if not articles:
        return json.dumps({"count": 0, "message": f"No papers found for '{topic}'."})

    results = []
    for a in articles:
        results.append({
            "id": a["id"],
            "title": a["title"],
            "authors": a["authors"],
            "published": a["published"],
            "pdf_url": a["pdf_url"],
        })

    return json.dumps({"count": len(results), "papers": results}, indent=2)


@mcp.tool()
def get_paper(article_id: str) -> str:
    """
    Get full metadata for a specific arXiv paper by its ID.

    Args:
        article_id: The arXiv short ID (e.g. "2401.12345v2")

    Returns:
        JSON string with paper metadata, or an error message if not found
    """
    article = get_article_details(article_id)
    if not article:
        return json.dumps({"error": f"Paper '{article_id}' not found. Try searching first."})
    return json.dumps(article, indent=2)


@mcp.tool()
def summarize_paper(article_id: str) -> str:
    """
    Generate an AI-powered summary of a paper. Uses Gemini when available,
    falls back to extractive summarization.

    Args:
        article_id: The arXiv short ID of the paper to summarize

    Returns:
        A clear, concise summary of the paper
    """
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found. Search for papers first."
    summary = summarize_article(article)
    return summary or "Could not generate summary."


@mcp.tool()
def explain_paper(article_id: str) -> str:
    """
    Explain a paper in simple terms a 10-year-old could understand.
    Breaks down the problem, solution, and why it matters.

    Args:
        article_id: The arXiv short ID of the paper to explain

    Returns:
        A simple explanation with "The Problem", "What They Built", and "Why It's Cool"
    """
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found. Search for papers first."
    explanation = eli10(article)
    return explanation or "Could not generate explanation."


@mcp.tool()
def chat_about_paper(article_id: str, message: str) -> str:
    """
    Have an interactive conversation about a paper. The AI explains things
    like a friendly teacher talking to a 10-year-old.

    Args:
        article_id: The arXiv short ID of the paper to discuss
        message: Your question about the paper

    Returns:
        The AI's response explaining the paper
    """
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found. Search for papers first."

    result = chat_about_article(article, message, history=[], provider="gemini")
    return result.get("response", "Could not get a response.")


# --------------- MCP Resources ---------------

@mcp.resource("arxiv://topics")
def get_topics_resource() -> str:
    """List all research topics that have been searched and saved."""
    topics = list_all_topics()
    if not topics:
        return "No topics saved yet. Use the search_arxiv tool to find papers first."

    lines = ["# Saved Research Topics\n"]
    for topic in topics:
        lines.append(f"- {topic.replace('_', ' ').title()}")
    lines.append(f"\nTotal: {len(topics)} topics")
    return "\n".join(lines)


@mcp.resource("arxiv://topic/{slug}")
def get_topic_resource(slug: str) -> str:
    """Get all saved papers for a specific research topic."""
    articles = get_articles_by_topic(slug)
    if not articles:
        return f"No papers found for topic '{slug}'."

    lines = [f"# Papers on {slug.replace('_', ' ').title()}\n"]
    lines.append(f"Total: {len(articles)} papers\n")

    for paper_id, paper in articles.items():
        lines.append(f"## {paper.get('title', 'Untitled')}")
        lines.append(f"- **ID**: {paper_id}")
        lines.append(f"- **Authors**: {', '.join(paper.get('authors', []))}")
        lines.append(f"- **Published**: {paper.get('published', 'Unknown')}")
        lines.append(f"- **PDF**: {paper.get('pdf_url', 'N/A')}")
        abstract = paper.get("summary", "")
        if abstract:
            lines.append(f"\n{abstract[:400]}...\n")
        lines.append("---\n")

    return "\n".join(lines)


@mcp.resource("arxiv://paper/{article_id}")
def get_paper_resource(article_id: str) -> str:
    """Get detailed metadata for a specific paper."""
    article = get_article_details(article_id)
    if not article:
        return f"Paper '{article_id}' not found."

    lines = [f"# {article.get('title', 'Untitled')}\n"]
    lines.append(f"**ID**: {article.get('id', article_id)}")
    lines.append(f"**Authors**: {', '.join(article.get('authors', []))}")
    lines.append(f"**Published**: {article.get('published', 'Unknown')}")
    lines.append(f"**PDF**: {article.get('pdf_url', 'N/A')}")
    lines.append(f"\n## Abstract\n\n{article.get('summary', 'No abstract available.')}")
    return "\n".join(lines)


# --------------- MCP Prompts ---------------

@mcp.prompt()
def research_summary(topic: str, num_papers: int = 5) -> str:
    """Generate a research summary by searching and summarizing papers on a topic."""
    return (
        f"Search for {num_papers} academic papers about '{topic}' using the search_arxiv tool. "
        f"Then summarize each paper using summarize_paper. "
        f"Finally, provide an overview of the research landscape:\n"
        f"- Common themes across papers\n"
        f"- Key findings and methods\n"
        f"- Research gaps or future directions\n\n"
        f"Present your findings in a clear, structured format."
    )


@mcp.prompt()
def explain_like_ten(topic: str) -> str:
    """Search for papers on a topic and explain them simply."""
    return (
        f"Search for papers about '{topic}' using search_arxiv. "
        f"Pick the most relevant paper and use explain_paper to get a simple explanation. "
        f"Then add your own simple explanation of why this research matters, "
        f"using everyday examples a 10-year-old would understand."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
