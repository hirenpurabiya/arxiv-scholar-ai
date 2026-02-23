"""
Article Finder module for ArXiv Scholar AI.
Searches arXiv for academic papers and stores their metadata locally.
"""

import arxiv
import json
import os
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from .config import RESEARCH_DIR, DEFAULT_MAX_RESULTS

logger = logging.getLogger(__name__)

SORT_CRITERIA = {
    "relevance": arxiv.SortCriterion.Relevance,
    "date": arxiv.SortCriterion.SubmittedDate,
    "updated": arxiv.SortCriterion.LastUpdatedDate,
}

FETCH_MULTIPLIER = 3
MAX_FETCH_COUNT = 25


def _parse_date(yyyymmdd: str) -> date:
    """Parse YYYYMMDD string into a date object."""
    return datetime.strptime(yyyymmdd, "%Y%m%d").date()


def _filter_by_date(
    articles: List[Dict[str, Any]],
    date_from: Optional[str],
    date_to: Optional[str],
) -> List[Dict[str, Any]]:
    """Filter articles whose published date falls within the range."""
    if not date_from and not date_to:
        return articles

    from_date = _parse_date(date_from) if date_from else date.min
    to_date = _parse_date(date_to) if date_to else date.max

    filtered = []
    for article in articles:
        try:
            pub = date.fromisoformat(article["published"])
            if from_date <= pub <= to_date:
                filtered.append(article)
        except (ValueError, KeyError):
            pass

    return filtered


def find_articles(
    topic: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    sort_by: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search arXiv for articles matching a topic and store their metadata.

    When date filters are provided, fetches extra results from arXiv and
    filters locally by published date. ArXiv's submittedDate query filter
    is unreliable, so we enforce it ourselves.

    Args:
        topic: The search query
        max_results: Maximum number of articles to return
        sort_by: Sort order - "relevance", "date", or "updated"
        date_from: Start date in YYYYMMDD format (inclusive)
        date_to: End date in YYYYMMDD format (inclusive)

    Returns:
        List of article metadata dicts, at most max_results items
    """
    client = arxiv.Client(
        page_size=20,
        delay_seconds=3,
        num_retries=3,
    )

    has_date_filter = bool(date_from or date_to)
    fetch_count = max_results * FETCH_MULTIPLIER if has_date_filter else max_results
    fetch_count = min(fetch_count, MAX_FETCH_COUNT)

    sort_criterion = SORT_CRITERIA.get(sort_by, arxiv.SortCriterion.Relevance)

    search = arxiv.Search(
        query=topic,
        max_results=fetch_count,
        sort_by=sort_criterion,
    )

    results = client.results(search)

    topic_slug = topic.lower().strip().replace(" ", "_")
    topic_dir = os.path.join(RESEARCH_DIR, topic_slug)
    os.makedirs(topic_dir, exist_ok=True)

    metadata_path = os.path.join(topic_dir, "articles.json")

    existing_data = {}
    try:
        with open(metadata_path, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}

    all_articles = []
    for result in results:
        article_id = result.get_short_id()

        article_metadata = {
            "id": article_id,
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary,
            "pdf_url": str(result.pdf_url),
            "published": str(result.published.date()),
            "topic": topic,
        }

        existing_data[article_id] = article_metadata
        all_articles.append(article_metadata)

    with open(metadata_path, "w") as f:
        json.dump(existing_data, f, indent=2)

    if has_date_filter:
        articles = _filter_by_date(all_articles, date_from, date_to)
    else:
        articles = all_articles

    articles = articles[:max_results]

    logger.info(
        f"Found {len(all_articles)} from arXiv, {len(articles)} after date filter "
        f"for topic '{topic}' (date_from={date_from}, date_to={date_to})"
    )

    return articles
