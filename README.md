# ArXiv Scholar AI

**AI-powered research paper discovery, summarization, and interactive chat — with a full MCP (Model Context Protocol) integration.**

Search [arXiv](https://arxiv.org/) for academic papers on any topic, get AI-powered summaries, and chat about papers with an "Explain Like I'm 10" AI tutor. Includes an MCP server and client that expose all capabilities as standardized tools, resources, and prompts.

**Live Demo:** [arxiv-scholar-ai.vercel.app](https://arxiv-scholar-ai.vercel.app)

---

## Features

- **Smart Search** -- Search arXiv's 2M+ papers with date filtering and sorting
- **AI Summarization** -- Gemini-powered summaries with local extraction fallback
- **Explain Like I'm 10** -- Interactive chat that explains papers in simple terms
- **MCP Server** -- Exposes search, summarize, explain, and chat as MCP tools (stdio + SSE)
- **MCP Client** -- CLI agent that connects to the MCP server with LLM-driven tool calling
- **MCP Resources** -- Browse saved topics and papers via standard MCP resource URIs
- **MCP Prompts** -- Pre-built prompt templates for research workflows
- **PDF Links** -- Direct links to download the full paper PDF
- **Topic Organization** -- Articles saved and organized by topic
- **Beautiful UI** -- Clean, professional interface built with Next.js and Tailwind CSS
- **REST API** -- Full FastAPI backend with retry-friendly error handling

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Next.js        │     │   FastAPI         │     │   arXiv API  │
│   Frontend       │────▶│   Backend (REST)  │────▶│   (papers)   │
│   (React + TS)   │     │   (Python)        │     └──────────────┘
└──────────────────┘     │                   │
                         │                   │     ┌──────────────┐
                         │                   │────▶│ Gemini API   │
                         │                   │     │ (AI/chat)    │
                         └──────────────────┘     └──────────────┘

┌──────────────────┐     ┌──────────────────┐
│   MCP Client     │     │   MCP Server     │     Wraps the same
│   (CLI agent     │────▶│   (FastMCP)      │────▶ backend functions
│    + Gemini)     │     │   stdio / SSE    │     as MCP tools
└──────────────────┘     └──────────────────┘
```

---

## Tech Stack

| Layer      | Technology                                     |
|------------|------------------------------------------------|
| Frontend   | Next.js, React, TypeScript, Tailwind CSS       |
| Backend    | Python, FastAPI, Pydantic                      |
| AI         | Google Gemini (free tier)                       |
| MCP        | FastMCP, MCP SDK (stdio + SSE transports)      |
| Data       | arXiv API via `arxiv` library                  |
| Deployment | Vercel (frontend), Render (backend)            |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Google API key](https://aistudio.google.com/apikey) (free — for AI summaries and chat)

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

# Set your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

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

The MCP layer wraps the existing backend functions as standardized tools that any MCP-compatible client (Claude Desktop, Cursor, custom agents) can use.

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

## REST API Endpoints

| Method | Endpoint                      | Description                          |
|--------|-------------------------------|--------------------------------------|
| GET    | `/api/search?topic=...`       | Search arXiv for articles            |
| GET    | `/api/article/{article_id}`   | Get details for a specific article   |
| GET    | `/api/summarize/{article_id}` | Generate AI summary for an article   |
| POST   | `/api/chat`                   | Chat about a paper (ELI10)           |
| GET    | `/api/topics`                 | List all searched topics             |
| GET    | `/api/topics/{topic_slug}`    | Get all articles for a topic         |

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
│       ├── summarizer.py      # Gemini AI summarization + local fallback
│       └── chat_engine.py     # Gemini-powered interactive chat
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout
│   │   │   └── page.tsx       # Main search page
│   │   ├── components/
│   │   │   ├── SearchBar.tsx    # Search input
│   │   │   ├── SearchFilters.tsx # Sorting and date filters
│   │   │   ├── ArticleCard.tsx  # Article preview card
│   │   │   ├── ArticleDetail.tsx # Full article view + AI features
│   │   │   └── ELI10Chat.tsx   # Interactive chat component
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
