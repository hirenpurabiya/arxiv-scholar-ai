# ArXiv Scholar AI

**AI-powered research paper discovery, summarization, and interactive chat — with a full MCP (Model Context Protocol) integration.**

Search [arXiv](https://arxiv.org/) for academic papers on any topic, get AI-powered summaries, and chat about papers with an "Explain Like I'm 10" AI tutor. Includes an MCP server and client that expose all capabilities as standardized tools, resources, and prompts.

> **LLM-agnostic architecture.** Currently uses Google Gemini (free tier). The AI layer is swappable — plug in OpenAI, Anthropic, xAI, Meta Llama, AWS Bedrock, or any LLM by changing a single API call.

**Live Demo:** [arxiv-scholar-ai.vercel.app](https://arxiv-scholar-ai.vercel.app)
**MCP Server:** [huggingface.co/spaces/hirenpurabiya/arxiv-scholar-ai](https://huggingface.co/spaces/hirenpurabiya/arxiv-scholar-ai) — connect from Claude Desktop, Cursor, or any MCP client

---

## Features

- **MCP Playground** -- Live AI agent demo on the landing page: type a query and watch the AI reason, pick tools, and compose an answer in real-time ([try it](https://arxiv-scholar-ai.vercel.app))
- **Smart Search** -- Search arXiv's 2M+ papers with date filtering and sorting
- **AI Summarization** -- LLM-powered summaries with local extraction fallback
- **Explain Like I'm 10** -- Interactive chat that explains papers in simple terms
- **MCP Server** -- Exposes search, summarize, explain, and chat as MCP tools (stdio + SSE)
- **MCP Client** -- CLI agent that connects to the MCP server with AI-driven tool calling
- **MCP Resources** -- Browse saved topics and papers via standard MCP resource URIs
- **MCP Prompts** -- Pre-built prompt templates for research workflows
- **PDF Links** -- Direct links to download the full paper PDF
- **Topic Organization** -- Articles saved and organized by topic
- **Beautiful UI** -- Clean, professional interface built with Next.js and Tailwind CSS
- **REST API** -- Full FastAPI backend with retry-friendly error handling

---

## Architecture

```
┌──────────────────┐     ┌──────────────────────────────────────────┐
│   Next.js        │     │   FastAPI Backend (Render)               │
│   Frontend       │     │                                          │
│   (React + TS)   │     │  ┌─────────────────┐  ┌──────────────┐  │
│                  │     │  │  /api/mcp-query  │  │  MCP Server  │  │
│  MCP Playground  │SSE  │  │  (MCP Agent)     │  │  (FastMCP)   │  │
│  (live agent UI) │────▶│  │                  │──│  /mcp/sse    │  │
└──────────────────┘     │  │  Connects as     │  │              │  │
                         │  │  SSE MCP client  │  │  5 tools     │  │
┌──────────────────┐     │  └─────────────────┘  │  3 resources  │  │
│   MCP Client     │     │                       │  2 prompts    │  │
│   (CLI agent     │────▶│                       │              │  │     ┌──────────────┐
│    + LLM)  stdio │     │                       └──────┬───────┘  │────▶│  arXiv API   │
└──────────────────┘     │                              │          │     └──────────────┘
                         └──────────────────────────────┘          │
Any MCP client                                                     │     ┌──────────────┐
(Claude Desktop,         Agent agentic loop:                       │────▶│  LLM API     │
 Cursor, custom)         LLM picks tool → session.call_tool()     │     │  (Gemini)    │
can also connect         → MCP server executes → loop or answer         └──────────────┘
```

---

## Tech Stack

| Layer      | Technology                                     |
|------------|------------------------------------------------|
| Frontend   | Next.js, React, TypeScript, Tailwind CSS       |
| Backend    | Python, FastAPI, Pydantic                      |
| AI         | LLM-powered (currently Gemini free tier; swappable) |
| MCP        | FastMCP, MCP SDK (stdio + SSE transports)      |
| Data       | arXiv API via `arxiv` library                  |
| Deployment | Vercel (frontend), Render (backend), Hugging Face (MCP server) |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An LLM API key (default: [Google Gemini free tier](https://aistudio.google.com/apikey); any LLM works)

### 1. Clone the repo

```bash
git clone https://github.com/hirenpurabiya/arxiv-scholar-ai.git
cd arxiv-scholar-ai
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set your LLM API key
cp .env.example .env
# Edit .env and add your API key (default: GOOGLE_API_KEY for Gemini free tier)

# Run the server
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API documentation.

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

### 4. Try the MCP Server (optional)

```bash
cd backend

# Run the stdio server directly
python mcp_server.py

# Or test with the MCP inspector
npx @modelcontextprotocol/inspector python mcp_server.py

# Or start the SSE remote server
python mcp_remote.py
```

### 5. Try the MCP Client (optional)

```bash
cd backend
python mcp_client.py
# Then type: "Find papers about transformers" and watch it call tools
```

---

## MCP Integration

The MCP server is mounted on the FastAPI app at `/mcp/sse`. The web agent connects to it as a real SSE client -- tools are discovered dynamically and executed through the MCP protocol. Any MCP-compatible client (Claude Desktop, Cursor, custom agents) can also connect.

### Tools

| Tool               | Description                                    |
|--------------------|------------------------------------------------|
| `search_arxiv`     | Search arXiv with topic, date, and sort filters |
| `get_paper`        | Get metadata for a specific paper by ID        |
| `summarize_paper`  | AI-powered summary of a paper                  |
| `explain_paper`    | Explain a paper like you're 10 years old       |
| `chat_about_paper` | Interactive Q&A about a paper                  |

### Resources

| URI Pattern               | Description                        |
|---------------------------|------------------------------------|
| `arxiv://topics`          | List all saved research topics     |
| `arxiv://topic/{slug}`    | Papers for a specific topic        |
| `arxiv://paper/{id}`      | Full metadata for a specific paper |

### Prompts

| Prompt              | Description                                      |
|---------------------|--------------------------------------------------|
| `research_summary`  | Search + summarize papers on a topic             |
| `explain_like_ten`  | Find a paper and explain it simply               |

---

## MCP Playground (Live Demo)

Visit [arxiv-scholar-ai.vercel.app](https://arxiv-scholar-ai.vercel.app) to see the MCP agent in action. It's the first thing you see when you open the app.

Type any natural language query like:
- "Find the latest papers on transformer architecture and summarize the top one"
- "Search for papers about RAG and explain the best one like I'm 10"
- "What are the newest papers on LLM reasoning?"

The Thinking panel shows every step in real-time: which tools the AI picks, the arguments it sends, and the results that come back. Nothing is pre-recorded or simulated.

### How it works

1. Your query hits `/api/mcp-query` (SSE endpoint)
2. The MCP agent connects to the MCP server via SSE (`session.initialize()`)
3. Tools are discovered dynamically (`session.list_tools()`)
4. A **system instruction** tells the LLM: "You MUST use the available tools. Always search first, never answer from memory."
5. The LLM picks which tools to call (search, summarize, explain, etc.)
6. Tools execute through the MCP protocol (`session.call_tool()`) -- not direct function calls
7. The LLM reads results and may call more tools or compose the final answer
8. Every step streams to the browser as a Server-Sent Event

### Prompt engineering & resilience

- **System instruction** — Gemini receives a structured prompt that forces tool usage, preventing it from answering from memory
- **MCP prompt templates** — `research_summary` and `explain_like_ten` are reusable prompt templates discoverable via the MCP protocol
- **Retry with backoff** — automatic retry with increasing delay (5s, 10s, 15s) when Gemini rate limits hit
- **Rate limit detection** — agent stops the agentic loop immediately when arXiv or Gemini signals rate limiting, instead of retrying and compounding the problem
- **arXiv retry with backoff** — handles transient 429 errors with exponential delay (5s, 10s, 15s)

---

## MCP Inspector

Technical recruiters and developers can connect to the MCP server using Anthropic's [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
cd backend

# Start the MCP Inspector (opens a browser UI)
npx @modelcontextprotocol/inspector python mcp_server.py
```

The Inspector lets you:
- Browse all available tools, resources, and prompts
- Call tools interactively and inspect responses
- Test resource URIs like `arxiv://topics` and `arxiv://paper/{id}`
- Verify the MCP schema is correct

You can also connect via any MCP-compatible client (Claude Desktop, Cursor, custom agents) using the stdio server:

```json
{
  "mcpServers": {
    "arxiv-scholar-ai": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/arxiv-scholar-ai/backend"
    }
  }
}
```

### Remote MCP Server (Hugging Face)

The MCP server is also deployed on Hugging Face Spaces with a Gradio UI. Any MCP client can connect to it remotely — no local setup needed:

```json
{
  "mcpServers": {
    "arxiv-scholar-ai": {
      "url": "https://hirenpurabiya-arxiv-scholar-ai.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

Try it in the browser: [huggingface.co/spaces/hirenpurabiya/arxiv-scholar-ai](https://huggingface.co/spaces/hirenpurabiya/arxiv-scholar-ai)

---

## REST API Endpoints

| Method | Endpoint                      | Description                                  |
|--------|-------------------------------|----------------------------------------------|
| GET    | `/api/search?topic=...`       | Search arXiv for articles                    |
| GET    | `/api/article/{article_id}`   | Get details for a specific article           |
| GET    | `/api/summarize/{article_id}` | Generate AI summary for an article           |
| POST   | `/api/chat`                   | Chat about a paper (ELI10)                   |
| GET    | `/api/mcp-query?q=...`        | SSE stream: MCP agent reasoning + tools      |
| GET    | `/api/topics`                 | List all searched topics                     |
| GET    | `/api/topics/{topic_slug}`    | Get all articles for a topic                 |

---

## Project Structure

```
arxiv-scholar-ai/
├── backend/
│   ├── main.py                # FastAPI app and REST API routes
│   ├── mcp_server.py          # MCP server (stdio transport)
│   ├── mcp_client.py          # MCP client CLI agent
│   ├── mcp_remote.py          # MCP server (SSE transport for deployment)
│   ├── requirements.txt       # Python dependencies
│   └── src/
│       ├── config.py          # App configuration
│       ├── article_finder.py  # arXiv search with date filtering
│       ├── article_reader.py  # Article metadata retrieval
│       ├── summarizer.py      # LLM-powered summarization + local fallback
│       ├── chat_engine.py     # LLM-powered interactive chat
│       └── mcp_agent.py       # MCP SSE client + agentic loop (MCP Playground)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # MCP Playground (main landing page)
│   │   │   └── search/page.tsx # Traditional search page
│   │   ├── components/
│   │   │   ├── SearchBar.tsx    # Search input
│   │   │   ├── SearchFilters.tsx # Sorting and date filters
│   │   │   ├── ArticleCard.tsx  # Article preview card
│   │   │   ├── ArticleDetail.tsx # Full article view + AI features
│   │   │   ├── ELI10Chat.tsx   # Interactive chat component
│   │   │   └── MCPPlayground.tsx # Live MCP agent reasoning UI
│   │   └── lib/
│   │       ├── api.ts         # Backend API client with retry logic
│   │       └── types.ts       # TypeScript type definitions
│   └── package.json
├── docs/
│   └── learning-journal.md    # Concepts and lessons learned
└── README.md
```

---

## Learning Journal

Check out [`docs/learning-journal.md`](docs/learning-journal.md) for a collection of software engineering, AI, and computer science concepts documented along the way -- explained simply and concisely.

---

## License

MIT License -- see [LICENSE](LICENSE) for details.

---

Built by [Hiren Purabiya](https://github.com/hirenpurabiya)
