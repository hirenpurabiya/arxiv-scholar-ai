"""
Suggest a short arXiv-relevant topic from a user query (e.g. for "no papers found" hints).
Uses Gemini to infer a 1-3 word topic from random or off-topic questions.
"""

import logging
import re

import requests

from .config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MODEL = "gemini-2.0-flash-lite"


def suggest_topic(query: str) -> str | None:
    """
    Infer a short (1-3 word) research topic from the user's query, suitable for arXiv search.
    Returns None if API key is missing, request fails, or result is empty.
    """
    if not GOOGLE_API_KEY or not (query or "").strip():
        return None

    prompt = (
        "You are helping someone search for academic papers on arXiv. "
        "Given the user's message below, reply with ONLY a short phrase (1-4 words) "
        "that would be a good search topic for arXiv. Use lowercase. "
        "Examples: 'protein intake', 'transformer architecture', 'sleep and memory'. "
        "If the message is too vague or not research-related, reply with a single general word like 'science' or 'health'.\n\n"
        f"User message: {query.strip()}\n\n"
        "Reply with only the topic phrase, nothing else:"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    url = f"{API_BASE}/{MODEL}:generateContent?key={GOOGLE_API_KEY}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Topic suggest {MODEL}: {resp.status_code}")
            return None
        data = resp.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        text = (text or "").strip()
        # Keep only first line and sanitize
        text = text.split("\n")[0].strip()
        text = re.sub(r"[^\w\s\-]", "", text)[:50].strip()
        return text if text else None
    except Exception as e:
        logger.warning(f"Topic suggest {MODEL}: {e}")
        return None
