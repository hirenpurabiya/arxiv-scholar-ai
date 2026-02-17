"""
ArXiv Scholar AI - FastAPI Backend
Provides REST API endpoints for searching, reading, and summarizing arXiv papers.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.article_finder import find_articles
from src.article_reader import get_article_details, list_all_topics, get_articles_by_topic
from src.summarizer import summarize_article, explain_like_ten, summarize_with_claude
from src.chat_engine import chat_about_article
from src.config import DEFAULT_MAX_RESULTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ArXiv Scholar AI",
    description="AI-powered research paper discovery and summarization",
    version="1.0.0",
)

# Allow frontend to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Response Models ---

class ArticleResponse(BaseModel):
    id: str
    title: str
    authors: list[str]
    summary: str
    pdf_url: str
    published: str
    topic: str


class SearchResponse(BaseModel):
    topic: str
    count: int
    articles: list[ArticleResponse]


class SummaryResponse(BaseModel):
    article_id: str
    title: str
    ai_summary: Optional[str]


class TopicsResponse(BaseModel):
    topics: list[str]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    article_id: str
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    provider: str


# --- API Endpoints ---

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "app": "ArXiv Scholar AI", "version": "1.0.0"}


@app.get("/api/search", response_model=SearchResponse)
async def search_articles(
    topic: str = Query(..., description="The research topic to search for"),
    max_results: int = Query(DEFAULT_MAX_RESULTS, ge=1, le=20, description="Maximum number of results"),
):
    """
    Search arXiv for articles matching a topic.
    Results are saved locally for future reference.
    """
    try:
        articles = find_articles(topic=topic, max_results=max_results)
        return SearchResponse(
            topic=topic,
            count=len(articles),
            articles=[ArticleResponse(**a) for a in articles],
        )
    except Exception as e:
        logger.error(f"Search failed for topic '{topic}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/article/{article_id}", response_model=ArticleResponse)
async def read_article(article_id: str):
    """
    Get details for a specific article by its arXiv ID.
    """
    article = get_article_details(article_id)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{article_id}' not found. Try searching for it first.",
        )
    return ArticleResponse(**article)


@app.get("/api/summarize/{article_id}", response_model=SummaryResponse)
async def summarize(article_id: str):
    """
    Generate a free summary by extracting key sentences from the abstract.
    """
    article = get_article_details(article_id)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{article_id}' not found. Try searching for it first.",
        )

    ai_summary = summarize_article(article)

    return SummaryResponse(
        article_id=article_id,
        title=article.get("title", "Unknown"),
        ai_summary=ai_summary,
    )


@app.get("/api/eli10/{article_id}", response_model=SummaryResponse)
async def explain_simple(article_id: str):
    """
    Explain a paper like I'm 10 -- break it into simple parts.
    """
    article = get_article_details(article_id)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{article_id}' not found. Try searching for it first.",
        )

    simple_explanation = explain_like_ten(article)

    return SummaryResponse(
        article_id=article_id,
        title=article.get("title", "Unknown"),
        ai_summary=simple_explanation,
    )


@app.get("/api/summarize-ai/{article_id}", response_model=SummaryResponse)
async def summarize_claude(article_id: str):
    """
    Generate an AI-powered summary using Claude (requires API credits).
    """
    article = get_article_details(article_id)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{article_id}' not found. Try searching for it first.",
        )

    ai_summary = summarize_with_claude(article)

    return SummaryResponse(
        article_id=article_id,
        title=article.get("title", "Unknown"),
        ai_summary=ai_summary,
    )


@app.get("/api/topics", response_model=TopicsResponse)
async def get_topics():
    """
    List all topics that have been searched and saved.
    """
    topics = list_all_topics()
    return TopicsResponse(topics=topics)


@app.get("/api/topics/{topic_slug}")
async def get_topic_articles(topic_slug: str):
    """
    Get all saved articles for a specific topic.
    """
    articles = get_articles_by_topic(topic_slug)
    if not articles:
        raise HTTPException(
            status_code=404,
            detail=f"No articles found for topic '{topic_slug}'.",
        )
    return {
        "topic": topic_slug,
        "count": len(articles),
        "articles": list(articles.values()),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat about a paper -- Explain Like I'm 10 interactive chatbot.
    Uses Groq (primary) with Gemini fallback.
    """
    article = get_article_details(request.article_id)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{request.article_id}' not found. Try searching for it first.",
        )

    history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    result = chat_about_article(article, request.message, history)

    return ChatResponse(response=result["response"], provider=result["provider"])
