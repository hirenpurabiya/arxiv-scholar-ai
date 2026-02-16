"""
Summarizer module for ArXiv Scholar AI.
Uses Claude (Anthropic API) to generate concise summaries of research papers.
"""

import logging
from typing import Dict, Any, Optional

import anthropic

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS

logger = logging.getLogger(__name__)


def summarize_article(article_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate an AI-powered summary of a research paper using Claude.

    Args:
        article_data: Dictionary containing article metadata (title, authors, summary, etc.)

    Returns:
        A concise, readable summary string, or None if summarization fails
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY is not set. Cannot generate summary.")
        return None

    title = article_data.get("title", "Unknown Title")
    authors = ", ".join(article_data.get("authors", []))
    abstract = article_data.get("summary", "No abstract available.")
    published = article_data.get("published", "Unknown date")

    prompt = f"""You are a research assistant. Summarize this academic paper in 3-4 sentences 
that a smart non-expert could understand. Focus on: what problem it solves, 
the key approach, and why it matters.

Title: {title}
Authors: {authors}
Published: {published}

Abstract:
{abstract}

Provide a clear, concise summary:"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        summary = response.content[0].text
        logger.info(f"Generated summary for article: {title}")
        return summary

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error while summarizing '{title}': {e}")
        return f"Error generating summary: {e}"
    except Exception as e:
        logger.error(f"Unexpected error while summarizing '{title}': {e}")
        return f"Error generating summary: {e}"
