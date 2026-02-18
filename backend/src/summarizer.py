"""
Summarizer module for ArXiv Scholar AI.
Provides Gemini-powered summaries with free local fallback.
"""

import re
import logging
from typing import Dict, Any, Optional

import requests

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS, GOOGLE_API_KEY

logger = logging.getLogger(__name__)


def _extract_key_sentences(abstract: str, max_sentences: int = 5) -> str:
    """
    Extract the most important sentences from an abstract.
    Prioritizes first sentence, sentences with key phrases, and conclusion.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', abstract) if s.strip()]

    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    key_phrases = [
        "we propose", "we present", "we introduce", "we develop",
        "we demonstrate", "we show", "our method", "our approach",
        "this paper", "this work", "results show", "experiments show",
        "outperforms", "achieves", "state-of-the-art", "novel",
        "significantly", "improve", "key finding", "main contribution",
    ]

    scored = []
    for i, sentence in enumerate(sentences):
        score = 0
        lower = sentence.lower()

        if i == 0:
            score += 3
        if i == len(sentences) - 1:
            score += 2

        for phrase in key_phrases:
            if phrase in lower:
                score += 1

        scored.append((score, i, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = sorted(scored[:max_sentences], key=lambda x: x[1])

    return " ".join(s[2] for s in top)


def _simplify_for_kids(abstract: str) -> str:
    """
    Create a simple 'Explain Like I'm 10' version of the abstract.
    Uses pattern matching to identify what the paper does and simplify it.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', abstract) if s.strip()]

    what_it_does = ""
    the_problem = ""
    why_it_matters = ""

    for sentence in sentences:
        lower = sentence.lower()

        if not the_problem and any(w in lower for w in ["problem", "challenge", "difficult", "limitation", "issue", "lack", "struggle", "hard to"]):
            the_problem = sentence

        if not what_it_does and any(w in lower for w in ["we propose", "we present", "we introduce", "we develop", "this paper", "this work", "we design", "we create", "our method", "our approach"]):
            what_it_does = sentence

        if not why_it_matters and any(w in lower for w in ["achieve", "outperform", "improve", "result", "demonstrate", "show that", "state-of-the-art", "significantly", "better than"]):
            why_it_matters = sentence

    if not what_it_does and sentences:
        what_it_does = sentences[0]
    if not why_it_matters and len(sentences) > 1:
        why_it_matters = sentences[-1]

    parts = []

    if the_problem:
        parts.append(f"The Problem: {the_problem}")
    if what_it_does:
        parts.append(f"What They Built: {what_it_does}")
    if why_it_matters:
        parts.append(f"Why It's Cool: {why_it_matters}")

    if not parts:
        return f"This paper is about: {sentences[0] if sentences else abstract[:200]}"

    return "\n\n".join(parts)


def _summarize_with_gemini(article_data: Dict[str, Any]) -> Optional[str]:
    """Generate a summary using Google Gemini (free tier)."""
    if not GOOGLE_API_KEY:
        return None

    title = article_data.get("title", "Unknown Title")
    abstract = article_data.get("summary", "")

    prompt = f"""Summarize this research paper in 5-8 sentences that a smart non-expert can understand.
Focus on: what problem it solves, the approach/method, key results, and why it matters.
Keep it simple and clear. No jargon.

Title: {title}

Abstract:
{abstract}

Summary:"""

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        logger.warning(f"Gemini summary failed: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Gemini summary error: {e}")

    return None


def summarize_article(article_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate a summary using Gemini (free), with local extraction as fallback.
    """
    abstract = article_data.get("summary", "")
    if not abstract:
        return "No abstract available for this article."

    gemini_summary = _summarize_with_gemini(article_data)
    if gemini_summary:
        return gemini_summary

    return _extract_key_sentences(abstract)


def explain_like_ten(article_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate an 'Explain Like I'm 10' version of the paper.
    Free, no API key needed.
    """
    abstract = article_data.get("summary", "")
    if not abstract:
        return "No abstract available for this article."

    return _simplify_for_kids(abstract)


def summarize_with_claude(article_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate an AI-powered summary using Claude (requires API key with credits).
    """
    if not ANTHROPIC_API_KEY:
        return "Claude AI summary requires an Anthropic API key. Use the free summary instead!"

    import anthropic

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

        return response.content[0].text

    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return f"Claude is unavailable right now. Error: {e}"
