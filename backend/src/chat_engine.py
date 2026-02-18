"""
Chat engine for ArXiv Scholar AI.
Powers the "Explain Like I'm 10" interactive chatbot.
Uses Google Gemini (free tier).
"""

import logging
from typing import Dict, Any, List

from .config import GOOGLE_API_KEY, GEMINI_MODEL

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


def _chat_with_gemini(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Send a chat request to Google Gemini."""
    if not GOOGLE_API_KEY:
        return {"success": False, "error_type": "not_configured", "error": "Google Gemini API key not configured."}

    try:
        from google import genai

        # Create client with API key
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Build the full prompt with system instruction and history
        full_prompt = system_prompt + "\n\n"
        
        # Add conversation history
        for msg in history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role_label}: {msg['content']}\n\n"
        
        # Add current message
        full_prompt += f"User: {message}\n\nAssistant:"

        # Generate response using the simple API
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )

        return {"success": True, "response": response.text}

    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Gemini chat failed: {e}")
        
        if "rate" in error_str or "429" in error_str or "quota" in error_str:
            return {"success": False, "error_type": "rate_limited", "error": str(e)}
        elif "billing" in error_str or "402" in error_str:
            return {"success": False, "error_type": "credits_exhausted", "error": str(e)}
        else:
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

    # Failed -- return friendly error
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
