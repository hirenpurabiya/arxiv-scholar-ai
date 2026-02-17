"""
Chat engine for ArXiv Scholar AI.
Powers the "Explain Like I'm 10" interactive chatbot.
Uses xAI Grok (primary) and Google Gemini (fallback) for AI chat.
"""

import logging
from typing import Dict, Any, List, Optional

from .config import XAI_API_KEY, GOOGLE_API_KEY

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


def _chat_with_grok(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Optional[str]:
    """Send a chat request to xAI Grok. Returns the response text or None on failure."""
    if not XAI_API_KEY:
        logger.info("xAI API key not configured, skipping Grok")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )

        messages = [{"role": "system", "content": system_prompt}]

        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="grok-3-mini-fast",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Grok chat failed: {e}")
        return None


def _chat_with_gemini(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Optional[str]:
    """Send a chat request to Google Gemini. Returns the response text or None on failure."""
    if not GOOGLE_API_KEY:
        logger.info("Google API key not configured, skipping Gemini")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)

        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(msg["content"])],
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(message)],
            )
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=300,
            ),
        )

        return response.text

    except Exception as e:
        logger.error(f"Gemini chat failed: {e}")
        return None


def chat_about_article(
    article: Dict[str, Any],
    message: str,
    history: List[Dict[str, str]],
) -> Dict[str, str]:
    """
    Chat about a paper using xAI Grok (primary) with Gemini fallback.

    Args:
        article: The paper's metadata dict (title, authors, summary, etc.)
        message: The user's current message
        history: List of previous messages, each with "role" and "content"

    Returns:
        Dict with "response" (the AI's answer) and "provider" (which AI answered)
    """
    system_prompt = _build_system_prompt(article)

    # Try xAI Grok first
    response = _chat_with_grok(system_prompt, message, history)
    if response:
        return {"response": response, "provider": "grok"}

    # Fall back to Google Gemini
    response = _chat_with_gemini(system_prompt, message, history)
    if response:
        return {"response": response, "provider": "gemini"}

    # Both failed
    return {
        "response": "I can't connect to any AI service right now. Please make sure XAI_API_KEY or GOOGLE_API_KEY is set in the server environment.",
        "provider": "none",
    }
