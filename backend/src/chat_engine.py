"""
Chat engine for ArXiv Scholar AI.
Powers the "Explain Like I'm 10" interactive chatbot.
Supports xAI Grok, Google Gemini, and Anthropic Claude.
"""

import logging
from typing import Dict, Any, List, Optional, Literal

from .config import XAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY, CLAUDE_MODEL

logger = logging.getLogger(__name__)

# Type for AI providers
AIProvider = Literal["grok", "gemini", "claude"]

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
) -> Dict[str, Any]:
    """Send a chat request to xAI Grok."""
    if not XAI_API_KEY:
        return {"success": False, "error_type": "not_configured", "error": "xAI Grok API key not configured."}

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
            model="grok-3-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7,
        )

        return {"success": True, "response": response.choices[0].message.content}

    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Grok chat failed: {e}")
        
        if "rate" in error_str or "429" in error_str:
            return {"success": False, "error_type": "rate_limited", "error": str(e)}
        elif "credit" in error_str or "balance" in error_str or "402" in error_str or "payment" in error_str:
            return {"success": False, "error_type": "credits_exhausted", "error": str(e)}
        else:
            return {"success": False, "error_type": "unknown", "error": str(e)}


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


def _chat_with_claude(
    system_prompt: str,
    message: str,
    history: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Send a chat request to Anthropic Claude."""
    if not ANTHROPIC_API_KEY:
        return {"success": False, "error_type": "not_configured", "error": "Anthropic Claude API key not configured."}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        messages = []
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=300,
            system=system_prompt,
            messages=messages,
        )

        return {"success": True, "response": response.content[0].text}

    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Claude chat failed: {e}")
        
        if "rate" in error_str or "429" in error_str:
            return {"success": False, "error_type": "rate_limited", "error": str(e)}
        elif "credit" in error_str or "balance" in error_str or "402" in error_str or "billing" in error_str:
            return {"success": False, "error_type": "credits_exhausted", "error": str(e)}
        else:
            return {"success": False, "error_type": "unknown", "error": str(e)}


# Mapping of provider names to their chat functions
PROVIDER_FUNCTIONS = {
    "grok": _chat_with_grok,
    "gemini": _chat_with_gemini,
    "claude": _chat_with_claude,
}

# Friendly suggestions when a provider fails
PROVIDER_SUGGESTIONS = {
    "grok": {
        "credits_exhausted": "Grok ran out of credits! Try Gemini (it's free) or Claude.",
        "rate_limited": "Grok is rate limited. Wait a moment or try Gemini.",
        "not_configured": "Grok API key not set. Try Gemini or Claude instead.",
        "unknown": "Grok had an error. Try Gemini or Claude instead.",
    },
    "gemini": {
        "credits_exhausted": "Gemini quota exceeded! Try Grok or Claude.",
        "rate_limited": "Gemini is rate limited. Wait a moment or try Grok.",
        "not_configured": "Gemini API key not set. Try Grok or Claude instead.",
        "unknown": "Gemini had an error. Try Grok or Claude instead.",
    },
    "claude": {
        "credits_exhausted": "Claude credits exhausted! Try Gemini (it's free) or Grok.",
        "rate_limited": "Claude is rate limited. Wait a moment or try Gemini.",
        "not_configured": "Claude API key not set. Try Gemini (free) or Grok instead.",
        "unknown": "Claude had an error. Try Gemini or Grok instead.",
    },
}


def chat_about_article(
    article: Dict[str, Any],
    message: str,
    history: List[Dict[str, str]],
    provider: AIProvider = "grok",
) -> Dict[str, Any]:
    """
    Chat about a paper using the specified AI provider.

    Args:
        article: The paper's metadata dict (title, authors, summary, etc.)
        message: The user's current message
        history: List of previous messages, each with "role" and "content"
        provider: Which AI to use ("grok", "gemini", or "claude")

    Returns:
        Dict with:
        - "response": the AI's answer (or error message)
        - "provider": which AI answered
        - "error_type": type of error if failed (optional)
        - "suggestion": friendly suggestion if failed (optional)
    """
    system_prompt = _build_system_prompt(article)

    # Get the chat function for the requested provider
    chat_fn = PROVIDER_FUNCTIONS.get(provider)
    if not chat_fn:
        return {
            "response": f"Unknown provider: {provider}. Use 'grok', 'gemini', or 'claude'.",
            "provider": "none",
            "error_type": "unknown",
            "suggestion": "Try selecting Grok, Gemini, or Claude.",
        }

    # Try the requested provider
    result = chat_fn(system_prompt, message, history)

    if result["success"]:
        return {"response": result["response"], "provider": provider}

    # Provider failed -- return error with helpful suggestion
    error_type = result.get("error_type", "unknown")
    suggestion = PROVIDER_SUGGESTIONS.get(provider, {}).get(error_type, "Try a different AI.")

    return {
        "response": suggestion,
        "provider": "none",
        "error_type": error_type,
        "suggestion": suggestion,
    }
