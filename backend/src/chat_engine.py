"""
Chat engine for ArXiv Scholar AI.
Powers the "Explain Like I'm 10" interactive chatbot.
Uses Google Gemini (free tier).
"""

import logging
from typing import Dict, Any, List

from .config import GOOGLE_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a friendly teacher who explains research papers to a 10-year-old kid.

Rules:
- Use simple words. No jargon. If you must use a big word, explain it right away.
- Use examples from everyday life (school, games, cooking, sports, animals).
- Keep answers short -- 2-4 sentences max, unless the user asks for more detail.
- Use analogies. For example: "A neural network is like a brain made of math."
- If the user asks a follow-up, answer it simply using the paper as context.
- Be encouraging and fun. Use phrases like "Great question!" or "Here's the cool part..."
- Never make things up. If the paper doesn't cover something, say so.

Here is the paper you are explaining:

Title: {title}
Authors: {authors}
Published: {published}

Abstract:
{abstract}
"""


def _build_system_prompt(article: Dict[str, Any]) -> str:
    """Build the system prompt with the paper's details filled in."""
    return SYSTEM_PROMPT.format(
        title=article.get("title", "Unknown Title"),
        authors=", ".join(article.get("authors", [])),
        published=article.get("published", "Unknown date"),
        abstract=article.get("summary", "No abstract available."),
    )


GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash"]


def _chat_with_gemini(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Send a chat request to Google Gemini via direct REST API."""
    if not GOOGLE_API_KEY:
        return {"success": False, "error_type": "not_configured", "error": "Google Gemini API key not configured."}

    import requests

    full_prompt = system_prompt + "\n\n"
    for msg in history:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        full_prompt += f"{role_label}: {msg['content']}\n\n"
    full_prompt += f"User: {message}\n\nAssistant:"

    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    last_error = None

    for model_name in GEMINI_MODELS:
        for api_version in ["v1", "v1beta"]:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={GOOGLE_API_KEY}"
            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"Gemini success: model={model_name}, api={api_version}")
                    return {"success": True, "response": text}
                else:
                    last_error = f"{resp.status_code}: {resp.text[:300]}"
                    logger.warning(f"Gemini {model_name} ({api_version}): {resp.status_code}")
            except requests.exceptions.Timeout:
                last_error = "Request timed out"
                logger.warning(f"Gemini {model_name} ({api_version}): timeout")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Gemini {model_name} ({api_version}): {e}")

    logger.error(f"All Gemini models failed. Last error: {last_error}")
    error_str = (last_error or "").lower()
    if "429" in error_str or "quota" in error_str or "rate" in error_str:
        return {"success": False, "error_type": "rate_limited", "error": last_error}
    return {"success": False, "error_type": "unknown", "error": last_error}


OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _chat_with_openai(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Send a chat request to OpenAI as fallback when Gemini fails."""
    if not OPENAI_API_KEY:
        return {"success": False, "error_type": "not_configured", "error": "OpenAI API key not configured."}

    import requests

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    payload = {"model": OPENAI_MODEL, "messages": messages, "temperature": 0.7}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

    try:
        resp = requests.post(OPENAI_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"]
            logger.info(f"OpenAI chat success: model={OPENAI_MODEL}")
            return {"success": True, "response": text}
        else:
            last_error = f"OpenAI {resp.status_code}: {resp.text[:300]}"
            logger.warning(f"OpenAI {OPENAI_MODEL}: {resp.status_code}")
            return {"success": False, "error_type": "unknown", "error": last_error}
    except requests.exceptions.Timeout:
        return {"success": False, "error_type": "unknown", "error": "OpenAI request timed out"}
    except Exception as e:
        return {"success": False, "error_type": "unknown", "error": str(e)}


def chat_about_article(
    article: Dict[str, Any],
    message: str,
    history: List[Dict[str, str]],
    provider: str = "gemini",
) -> Dict[str, Any]:
    """
    Chat about a paper using Google Gemini.

    Args:
        article: The paper's metadata dict (title, authors, summary, etc.)
        message: The user's current message
        history: List of previous messages, each with "role" and "content"
        provider: Kept for API compatibility (always uses Gemini)

    Returns:
        Dict with:
        - "response": the AI's answer (or error message)
        - "provider": "gemini"
        - "error_type": type of error if failed (optional)
        - "suggestion": friendly suggestion if failed (optional)
    """
    system_prompt = _build_system_prompt(article)

    result = _chat_with_gemini(system_prompt, message, history)

    if result["success"]:
        return {"response": result["response"], "provider": "gemini"}

    # Gemini failed — try OpenAI fallback
    if OPENAI_API_KEY:
        logger.warning("Gemini chat failed, trying OpenAI fallback")
        openai_result = _chat_with_openai(system_prompt, message, history)
        if openai_result["success"]:
            return {"response": openai_result["response"], "provider": "openai"}

    # Both failed -- return friendly error
    error_type = result.get("error_type", "unknown")
    
    suggestions = {
        "rate_limited": "The AI is busy right now. Please wait a moment and try again.",
        "credits_exhausted": "The AI is temporarily unavailable. Please try again later.",
        "not_configured": "The AI is not available right now.",
        "unknown": "Something went wrong. Please try again.",
    }
    
    suggestion = suggestions.get(error_type, "Please try again.")

    return {
        "response": suggestion,
        "provider": "none",
        "error_type": error_type,
        "suggestion": suggestion,
    }
