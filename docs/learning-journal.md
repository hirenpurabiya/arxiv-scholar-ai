# Learning Journal

A collection of software engineering, computer science, and AI concepts learned while building the ArXiv Paper Finder project. Each concept is explained simply and concisely -- like you're explaining to a 10-year-old.

---

## Progress Tracker

**Current Focus:** MCP (Model Context Protocol)

| Topic | Status | Notes |
|-------|--------|-------|
| MCP Basics | Completed | Protocol overview, architecture |
| MCP Server | Completed | FastMCP, tools, stdio transport |
| MCP Client | Completed | Sessions, tool discovery, agentic loop |
| Multi-Server | Completed | Connecting to multiple MCP servers |
| Resources & Prompts | Completed | Static/dynamic resources, prompt templates |
| Remote Deployment | Completed | SSE transport, cloud deployment |

*Last updated: 2026-02-17*

---

## Table of Contents

1. [Functions, Parameters, Type Hints, Return Types](#1-functions-parameters-type-hints-return-types)
2. [Dictionaries, Lists, Hash Maps -- and When to Use Each](#2-dictionaries-lists-hash-maps----and-when-to-use-each)
3. [Try/Except Error Handling and Defensive Programming](#3-tryexcept-error-handling-and-defensive-programming)
4. [File I/O, Context Managers, Serialization](#4-file-io-context-managers-serialization)
5. [JSON, JSON Schema, APIs](#5-json-json-schema-apis)
6. [The AI Agent Architecture (Brain + Hands Pattern)](#6-the-ai-agent-architecture-brain--hands-pattern)
7. [Tool Calling -- How Claude, ChatGPT, and Gemini Actually Work](#7-tool-calling----how-claude-chatgpt-and-gemini-actually-work)
8. [Idempotency, Race Conditions, Premature Optimization](#8-idempotency-race-conditions-premature-optimization)
9. [Single Responsibility Principle, Fail Fast, LBYL vs EAFP](#9-single-responsibility-principle-fail-fast-lbyl-vs-eafp)
10. [Dispatch Tables, Adapter Pattern, Method Chaining vs Module Navigation](#10-dispatch-tables-adapter-pattern-method-chaining-vs-module-navigation)
11. [Enums, Type Safety, Naming Conventions](#11-enums-type-safety-naming-conventions)
12. [Model Context Protocol (MCP) -- The USB-C of AI](#12-model-context-protocol-mcp----the-usb-c-of-ai)

---

## 1. Functions, Parameters, Type Hints, Return Types

### What is a function?

A function is like a **recipe card**. You give it a name, tell it what ingredients (inputs) it needs, and it does a specific job. You can reuse it over and over.

```python
def search_papers(topic: str, max_results: int = 5) -> List[str]:
```

### Parameters

Parameters are the **inputs** a function needs. Like telling a chef "make me a pizza with pepperoni":
- `topic: str` -- a required input (you must provide it)
- `max_results: int = 5` -- an optional input with a default value (if you don't say, it picks 5)

### Type Hints

The `: str` and `: int` parts are **labels** that say what type of data each parameter should be. They don't enforce anything -- they're like signs that help other people (and your future self) understand the code.

- `str` = text ("hello", "robots")
- `int` = whole numbers (5, 42)
- `float` = decimal numbers (3.14)
- `bool` = true or false
- `list` = a collection of items

### Return Types

`-> List[str]` is a promise: "this function will give back a list of strings." The `->` arrow means "returns."

- `->` at the top = a preview/label (informational, doesn't do anything)
- `return` inside the function = the actual action of giving back the value

### Key Principle: Single Responsibility

Great engineers write small, clear functions that do **one thing well**. This is the Single Responsibility Principle.

---

## 2. Dictionaries, Lists, Hash Maps -- and When to Use Each

### What is a dictionary?

A dictionary stores data as **key-value pairs**. Like a real dictionary where every word (key) has a definition (value):

```python
{"cat": "a small furry animal", "dog": "a loyal furry friend"}
```

### Why use a dictionary instead of a list?

A **list** is like a stack of papers -- to find something, you check each one (slow for large collections).

A **dictionary** is like a filing cabinet with labeled folders -- you go straight to the label you want (instant lookup).

### Same concept, different names

| Language | Name |
|---|---|
| Python | dictionary (dict) |
| Java | HashMap |
| JavaScript | Object / Map |
| C++ | unordered_map |
| JSON | object |

They all use **hashing** under the hood -- a math trick that converts a key into a location for instant lookup.

### When to use what

- **Dictionary** -- when you need to look up items by a unique name/key
- **List** -- when you need an ordered sequence of items
- **Set** -- when you need unique items with no duplicates

### Bonus: Automatic deduplication

Because dictionary keys must be unique, storing items by ID gives you **deduplication for free**. If you add the same key twice, it just overwrites -- no duplicates.

### MapReduce is NOT a dictionary

MapReduce is a way to **process** huge data across many computers (invented by Google). Dictionary/hash map is a way to **store** data. Totally different concepts.

---

## 3. Try/Except Error Handling and Defensive Programming

### What is try/except?

Programs crash when they hit errors. `try/except` catches errors and handles them gracefully instead of crashing:

```python
try:
    # Attempt something risky
    with open("file.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    # Backup plan if file doesn't exist
    data = {}
```

- **try** = "attempt this"
- **except** = "if it fails, do this instead"

### Always catch SPECIFIC errors

```python
# GOOD -- catch specific errors you expect
except (FileNotFoundError, json.JSONDecodeError):

# BAD -- catches everything, hides real bugs
except:
```

### Errors are classes

Every error in Python is a **class**. `FileNotFoundError` is a built-in class. `json.JSONDecodeError` is a class inside the `json` module. When errors happen, Python creates an object of that class and "throws" it.

### How to discover what errors can happen

1. **Run the code and see what breaks** -- the error message tells you the class name
2. **Read the documentation** -- it lists what errors each function can raise
3. **Think about what could go wrong** (comes with experience)
4. **Look at Python's error hierarchy** in the official docs

### Defensive programming

Always assume something can go wrong, and plan for it. Real-world software (apps, websites, services) can NEVER crash. Engineers use try/except to handle problems gracefully.

### Variable initialization

Always make sure variables exist and have a sensible starting value before you use them. `papers_info = {}` ensures we have a container ready even if the file doesn't exist.

---

## 4. File I/O, Context Managers, Serialization

### The `with` statement (context manager)

```python
with open(file_path, "r") as json_file:
    data = json.load(json_file)
```

`with` is like a responsible babysitter -- it opens the file, lets you use it, and **automatically closes it** when done, even if an error happens.

### Why files need to be closed

When a program opens a file, the operating system creates a **connection** (reserves memory, tracks position, sometimes locks the file). If you don't close it:
- Memory leaks
- File locks (other programs can't access it)
- Eventually your computer runs out of file handles

`with` prevents all of these by automatically closing.

### File modes

- `"r"` = read (just looking)
- `"w"` = write (erases everything, writes fresh)
- `"a"` = append (adds to the end without erasing)

### Serialization and deserialization

- **Serialization** = converting data from your program into a saveable/sendable format (like packing a suitcase)
- **Deserialization** = converting it back into usable program data (like unpacking)

```python
json.dump(data, file)   # Serialize: Python dict → JSON file
json.load(file)         # Deserialize: JSON file → Python dict
json.dumps(data)        # Serialize: Python dict → JSON string (s = string)
json.loads(text)        # Deserialize: JSON string → Python dict
```

### The Read-Modify-Write pattern

1. **Read** existing data from a file
2. **Modify** it (add, update, or delete)
3. **Write** it back

This pattern appears everywhere in software -- files, databases, APIs.

---

## 5. JSON, JSON Schema, APIs

### What is JSON?

JSON (JavaScript Object Notation) is a way to store data as text that both humans and computers can read. Despite the name, every language uses it.

```json
{
  "title": "Cool Paper",
  "authors": ["Alice", "Bob"],
  "published": "2025-01-15"
}
```

### JSON vs other formats

- **CSV** -- simple tables, but messy for nested data
- **XML** -- powerful but ugly and hard to read
- **JSON** -- clean, simple, perfect for structured data
- **Database** -- better for huge amounts of data

### What is JSON Schema?

A formal way to describe the **shape** of data. Used to tell AI models what tools they can use and what inputs those tools need. Types in JSON Schema:

| JSON Schema | Python equivalent |
|---|---|
| `"object"` | dict |
| `"string"` | str |
| `"integer"` | int |
| `"number"` | float |
| `"boolean"` | bool |
| `"array"` | list |

### What is an API?

API (Application Programming Interface) = your code sends a request over the internet to another computer, and it sends back a response. Almost every modern app works this way.

### Environment variables and security

NEVER put secrets (API keys, passwords) directly in code. Use a `.env` file that stays on your machine and `.gitignore` to keep it off GitHub.

```python
load_dotenv()  # Loads secrets from .env file
client = anthropic.Anthropic()  # Automatically uses the API key
```

---

## 6. The AI Agent Architecture (Brain + Hands Pattern)

### The core idea

AI models like Claude are the **brain** -- they think and make decisions. But they can't actually DO anything (search the web, open files, run code). Your code is the **hands** that execute those decisions.

```
CLAUDE (the brain):              YOUR CODE (the hands):
  ✓ Understands questions          ✓ Actually runs functions
  ✓ Decides which tool to use      ✓ Connects to external services
  ✓ Decides what args to pass      ✓ Saves files
  ✓ Reads results                  ✓ Sends results back to Claude
  ✓ Writes final answer
  ✗ Cannot run code                ✗ Doesn't decide what to do
  ✗ Cannot access internet         ✗ Just follows Claude's instructions
```

### The agentic loop

1. User asks a question
2. Claude decides to use a tool
3. Your code runs the tool
4. Your code sends results back to Claude
5. Claude reads results and either uses another tool or gives the final answer
6. Repeat until done

This is the **exact** architecture that powers ChatGPT plugins, Claude's tool use, and all modern AI agents.

---

## 7. Tool Calling -- How Claude, ChatGPT, and Gemini Actually Work

### Tool Schema (the menu)

You give the AI a "menu" of tools it can use, described in JSON Schema:

```python
tools = [
    {
        "name": "search_papers",
        "description": "Search for papers on arXiv",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to search for"}
            },
            "required": ["topic"]
        }
    }
]
```

The AI reads this menu and decides when and how to use each tool.

### The conversation flow

```
messages = [
    {"role": "user", "content": "Find papers about robots"},
    {"role": "assistant", "content": [tool_use block]},
    {"role": "user", "content": [tool_result]},
    {"role": "assistant", "content": "Here are the papers I found..."}
]
```

The full history must be sent every time so the AI has context.

### Tool IDs

Every tool call gets a unique ID (like a receipt number). When you send results back, you attach this ID so the AI knows which result belongs to which tool call. This matters when the AI makes multiple tool calls at once.

### Context management

The conversation history can't be infinite -- AI models have a **context window** (max tokens they can see at once). Managing this history (sliding window, summarization, external memory) is a key skill in AI engineering.

---

## 8. Idempotency, Race Conditions, Premature Optimization

### Idempotency

An operation is **idempotent** if running it multiple times gives the same result as running it once.

```python
# Idempotent -- safe to repeat
os.makedirs(path, exist_ok=True)  # Creates folder, or does nothing if it exists

# Not idempotent -- breaks on repeat
os.makedirs(path)  # CRASH if folder already exists!
```

Real-world example: payment systems use **idempotency keys** (unique IDs) to prevent charging customers twice if they accidentally tap "Pay" twice.

### Race conditions

When two things happen at the same time and compete with each other. Example: your code checks if a file exists (yes!), but another program deletes it in that split second before your code opens it -- CRASH!

### Premature optimization

A famous principle from Donald Knuth: *"Premature optimization is the root of all evil."*

Don't make code more complex to be "faster" unless you actually have a speed problem. Write it simple first, measure if it's slow, THEN optimize. For 5-10 papers, a simple approach is fine. For millions, you'd optimize.

---

## 9. Single Responsibility Principle, Fail Fast, LBYL vs EAFP

### Single Responsibility Principle

Each function should do **one thing well**. `search_papers()` searches and saves. `extract_info()` looks up details. They work together but each has a clear, focused job.

### Fail Fast

Design code to crash **immediately** when something is wrong, instead of silently continuing with bad data. Silent failures are the worst kind of bugs -- they corrupt data and you don't find out until much later.

### LBYL vs EAFP

Two styles of defensive programming:

- **LBYL (Look Before You Leap)** -- check first, then act:
  ```python
  if os.path.isfile(file_path):  # Check first
      open(file_path)             # Then act
  ```

- **EAFP (Easier to Ask Forgiveness than Permission)** -- just do it, handle errors if they happen:
  ```python
  try:
      open(file_path)             # Just try
  except FileNotFoundError:       # Handle if it fails
      pass
  ```

Python prefers EAFP, but you can use both together (belt AND suspenders).

### Early Return

Exit a function as soon as you have the answer, instead of continuing unnecessary work:

```python
if paper_id in papers_info:
    return papers_info[paper_id]  # Found it! Stop here.
# Only reaches here if NOT found -- keep searching
```

---

## 10. Dispatch Tables, Adapter Pattern, Method Chaining vs Module Navigation

### Dispatch table (lookup table)

Instead of long if/else chains, use a dictionary to map names to functions:

```python
mapping = {
    "search_papers": search_papers,
    "extract_info": extract_info
}
# Call dynamically:
mapping[tool_name](**tool_args)
```

Cleaner and easier to extend -- just add a new entry.

### Adapter pattern

A function that sits **between** two systems, translating between them. `execute_tool()` is an adapter between Claude (who sends tool names and args) and your Python functions (which expect specific parameters).

### Dictionary unpacking (`**`)

The `**` operator spreads a dictionary into function arguments:

```python
args = {"topic": "robots", "max_results": 5}
search_papers(**args)
# Same as: search_papers(topic="robots", max_results=5)
```

### Method chaining vs module navigation

**Method chaining** -- each step transforms data, `()` after each dot:
```python
topic.lower().replace(" ", "_")
# "Black Holes" → "black holes" → "black_holes"
```

**Module navigation** -- just finding a tool, `()` only at the end:
```python
os.path.join(PAPER_DIR, topic)
# os → path → join (navigating to the function)
```

Quick rule: `()` after each dot = chaining. `()` only at end = navigation.

---

## 11. Enums, Type Safety, Naming Conventions

### Enums

An enum (enumeration) is a **fixed list of choices** -- like a traffic light that can only be red, yellow, or green:

```python
sort_by = arxiv.SortCriterion.Relevance       # OK
sort_by = arxiv.SortCriterion.SubmittedDate    # OK
sort_by = arxiv.SortCriterion.Pizza            # ERROR! Not a valid choice.
```

### Type safety

Enums prevent mistakes. A plain variable accepts anything (including typos). An enum only accepts valid choices. This prevents bugs before they happen.

### Python naming conventions

- `my_variable` -- lowercase with underscores = variable or function (**snake_case**)
- `MyClass` -- capital first letters = class (**PascalCase**)
- `MAX_RESULTS` -- all caps = constant that never changes (**UPPER_SNAKE_CASE**)

Great engineers follow these conventions so anyone can tell "oh, that's a class" or "that's a variable" just by looking at the name.

---

## 12. Model Context Protocol (MCP) -- The USB-C of AI

### What is MCP?

MCP (Model Context Protocol) is a **standard** created by Anthropic that lets AI models (like Claude, Gemini, GPT) talk to external tools in a consistent way. Think of it like USB-C -- one plug that works with everything, instead of every device needing its own cable.

Before MCP, every AI app had to write custom code to connect to each tool. MCP says: "Here's one protocol everyone follows."

### The three building blocks

1. **Tools** -- Functions the AI can call (like "search_papers" or "summarize_paper"). The AI decides *when* to use them.

2. **Resources** -- Read-only data the AI can look at (like "show me all saved topics"). Think of these as files or database views the AI can browse.

3. **Prompts** -- Pre-built templates that guide the AI through a workflow (like "search for papers on X, summarize each one, then give an overview").

### MCP Server

The server **exposes** tools, resources, and prompts. It's like a restaurant menu -- it tells clients what's available.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_papers(topic: str) -> str:
    """Search for papers on arXiv."""
    # ... implementation ...
```

### MCP Client

The client **connects** to a server, discovers what's available, and calls tools on behalf of an LLM. It's the waiter that takes orders from the customer (LLM) and brings them to the kitchen (server).

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server = StdioServerParameters(command="python", args=["mcp_server.py"])
async with stdio_client(server) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("search_papers", {"topic": "robots"})
```

### Transport: stdio vs SSE

- **stdio** -- Server runs as a subprocess on the same machine. Input/output flows through stdin/stdout pipes. Fast, simple, used for local tools.

- **SSE (Server-Sent Events)** -- Server runs on a remote machine (like Render). Communication happens over HTTP. Used for deployed/shared servers.

Same protocol, different "wires." Like calling someone on the phone vs. walkie-talkie -- same conversation, different medium.

### The Agentic Loop with MCP

1. User asks a question
2. LLM sees the available MCP tools and decides which one to call
3. Client sends the tool call to the MCP server
4. Server runs the function and returns results
5. Client sends results back to the LLM
6. LLM either calls another tool or gives the final answer

This is the **exact** pattern behind Claude Desktop's tool use, Cursor's MCP integration, and production AI agents.

### Why MCP matters for your career

MCP is becoming the industry standard. Knowing how to build MCP servers and clients shows recruiters and hiring managers that you understand:
- How AI agents actually work under the hood
- Protocol design and standardization
- Client-server architecture
- Tool calling / function calling patterns
- How to make AI systems extensible and interoperable

---

*This journal grows as we learn. Each concept is a building block toward becoming a world-class AI engineer.*
