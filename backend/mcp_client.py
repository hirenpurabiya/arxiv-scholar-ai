"""
ArXiv Scholar AI - MCP Client

A CLI chatbot that connects to the MCP server and uses an LLM
(Google Gemini) to decide when to call tools. Demonstrates the
full MCP client flow: connect, discover tools, run an agentic loop.

Run:  python mcp_client.py
"""

import asyncio
import json
import logging
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import requests

load_dotenv()

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}"
    f":generateContent?key={GEMINI_API_KEY}"
)

MCP_SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "mcp_server.py")


def call_gemini(messages: list, tools: list | None = None) -> dict:
    """Call Gemini and return the parsed JSON response."""
    payload: dict = {"contents": messages}
    if tools:
        payload["tools"] = [{"functionDeclarations": tools}]

    resp = requests.post(GEMINI_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def format_tools_for_gemini(mcp_tools: list) -> list:
    """Convert MCP tool descriptors into Gemini function-declaration format."""
    declarations = []
    for tool in mcp_tools:
        schema = tool.inputSchema or {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        gemini_props = {}
        for name, prop in properties.items():
            prop_type = prop.get("type", "string").upper()
            type_map = {
                "STRING": "STRING",
                "INTEGER": "INTEGER",
                "NUMBER": "NUMBER",
                "BOOLEAN": "BOOLEAN",
                "ARRAY": "ARRAY",
                "OBJECT": "OBJECT",
            }
            gemini_props[name] = {
                "type": type_map.get(prop_type, "STRING"),
                "description": prop.get("description", ""),
            }

        declarations.append({
            "name": tool.name,
            "description": tool.description or "",
            "parameters": {
                "type": "OBJECT",
                "properties": gemini_props,
                "required": required,
            },
        })
    return declarations


def extract_response_text(response: dict) -> str | None:
    """Pull the text out of a Gemini response."""
    try:
        parts = response["candidates"][0]["content"]["parts"]
        for part in parts:
            if "text" in part:
                return part["text"]
    except (KeyError, IndexError):
        pass
    return None


def extract_tool_calls(response: dict) -> list:
    """Pull any function-call requests from a Gemini response."""
    calls = []
    try:
        parts = response["candidates"][0]["content"]["parts"]
        for part in parts:
            if "functionCall" in part:
                calls.append(part["functionCall"])
    except (KeyError, IndexError):
        pass
    return calls


async def run_agent():
    """Main agentic loop: connect to MCP server, discover tools, chat."""
    if not GEMINI_API_KEY:
        print("Error: GOOGLE_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_SCRIPT],
    )

    print("=" * 60)
    print("  ArXiv Scholar AI — MCP Client")
    print("  Type your questions. Type 'quit' to exit.")
    print("=" * 60)

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tool_list = await session.list_tools()
            tools = tool_list.tools
            gemini_tools = format_tools_for_gemini(tools)

            tool_names = [t.name for t in tools]
            print(f"\nConnected! Available tools: {', '.join(tool_names)}\n")

            conversation: list = []

            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                conversation.append({
                    "role": "user",
                    "parts": [{"text": user_input}],
                })

                response = call_gemini(conversation, gemini_tools)
                tool_calls = extract_tool_calls(response)

                while tool_calls:
                    conversation.append(response["candidates"][0]["content"])

                    function_responses = []
                    for fc in tool_calls:
                        fn_name = fc["name"]
                        fn_args = fc.get("args", {})
                        print(f"  [Calling tool: {fn_name}]")

                        result = await session.call_tool(fn_name, fn_args)
                        result_text = result.content[0].text if result.content else "No result."
                        function_responses.append({
                            "functionResponse": {
                                "name": fn_name,
                                "response": {"result": result_text},
                            }
                        })

                    conversation.append({
                        "role": "function",
                        "parts": function_responses,
                    })

                    response = call_gemini(conversation, gemini_tools)
                    tool_calls = extract_tool_calls(response)

                answer = extract_response_text(response)
                if answer:
                    conversation.append({
                        "role": "model",
                        "parts": [{"text": answer}],
                    })
                    print(f"\nAssistant: {answer}\n")
                else:
                    print("\nAssistant: (no response)\n")


if __name__ == "__main__":
    asyncio.run(run_agent())
