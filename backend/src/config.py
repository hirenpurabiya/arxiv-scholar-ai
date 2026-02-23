"""
Configuration and constants for ArXiv Scholar AI.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Directory where article metadata is stored
RESEARCH_DIR = "research_data"

# Anthropic API key for Claude-powered summarization
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Gemini API key for chat (free tier)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini model for chat (gemini-2.0-flash-lite has better rate limits for free tier)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# Default number of articles to return per search
DEFAULT_MAX_RESULTS = 5

# Claude model to use for summarization
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# Maximum tokens for Claude's response
MAX_TOKENS = 1024

# MCP server URL for SSE transport (agent connects here as an MCP client).
# On Render, PORT is set automatically; locally it defaults to 8000.
_port = os.getenv("PORT", "8000")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", f"http://localhost:{_port}/mcp/sse")
