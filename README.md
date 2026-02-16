# ArXiv Scholar AI

**AI-powered research paper discovery and summarization.**

Search [arXiv](https://arxiv.org/) for academic papers on any topic and get concise AI-powered summaries using Claude. Built with a modern full-stack architecture: Next.js frontend + Python FastAPI backend.

---

## Features

- **Smart Search** -- Search arXiv's database of 2M+ papers by any topic
- **AI Summarization** -- Get clear, concise summaries powered by Claude (Anthropic)
- **PDF Links** -- Direct links to download the full paper PDF
- **Topic Organization** -- Articles are saved and organized by topic for easy revisiting
- **Beautiful UI** -- Clean, modern interface built with Next.js and Tailwind CSS
- **REST API** -- Full API backend you can use independently

---

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Next.js        │     │   FastAPI         │     │   arXiv API  │
│   Frontend       │────▶│   Backend         │────▶│   (papers)   │
│   (React + TS)   │     │   (Python)        │     └──────────────┘
└──────────────────┘     │                   │
                         │                   │     ┌──────────────┐
                         │                   │────▶│ Claude API   │
                         │                   │     │ (summaries)  │
                         └──────────────────┘     └──────────────┘
```

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | Next.js 16, React, TypeScript, Tailwind CSS |
| Backend    | Python, FastAPI, Pydantic         |
| AI         | Claude (Anthropic API)            |
| Data       | arXiv API via `arxiv` library     |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/) (for AI summaries)

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
# Edit .env and add your ANTHROPIC_API_KEY

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

---

## API Endpoints

| Method | Endpoint                      | Description                          |
|--------|-------------------------------|--------------------------------------|
| GET    | `/api/search?topic=...`       | Search arXiv for articles            |
| GET    | `/api/article/{article_id}`   | Get details for a specific article   |
| GET    | `/api/summarize/{article_id}` | Generate AI summary for an article   |
| GET    | `/api/topics`                 | List all searched topics             |
| GET    | `/api/topics/{topic_slug}`    | Get all articles for a topic         |

---

## Project Structure

```
arxiv-scholar-ai/
├── backend/
│   ├── main.py                # FastAPI app and API routes
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variable template
│   └── src/
│       ├── config.py          # App configuration
│       ├── article_finder.py  # arXiv search logic
│       ├── article_reader.py  # Article metadata retrieval
│       └── summarizer.py      # Claude AI summarization
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout
│   │   │   └── page.tsx       # Main search page
│   │   ├── components/
│   │   │   ├── SearchBar.tsx    # Search input component
│   │   │   ├── ArticleCard.tsx  # Article preview card
│   │   │   └── ArticleDetail.tsx # Full article view + AI summary
│   │   └── lib/
│   │       ├── api.ts         # Backend API client
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
