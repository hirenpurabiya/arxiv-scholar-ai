"""
Article Finder module for ArXiv Scholar AI.
Searches arXiv for academic papers and stores their metadata locally.
"""

import arxiv
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .config import RESEARCH_DIR, DEFAULT_MAX_RESULTS

logger = logging.getLogger(__name__)

# Map sort options to arxiv SortCriterion
SORT_CRITERIA = {
    "relevance": arxiv.SortCriterion.Relevance,
    "date": arxiv.SortCriterion.SubmittedDate,
    "updated": arxiv.SortCriterion.LastUpdatedDate,
}


def find_articles(
    topic: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    sort_by: str = "relevance",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search arXiv for articles matching a topic and store their metadata.

    Args:
        topic: The search query (e.g., "transformer architecture", "reinforcement learning")
        max_results: Maximum number of articles to retrieve
        sort_by: How to sort results - "relevance", "date", or "updated"
        date_from: Start date filter in YYYYMMDD format (optional)
        date_to: End date filter in YYYYMMDD format (optional)

    Returns:
        List of article metadata dictionaries
    """
    client = arxiv.Client()

    # Build query with optional date range
    query = topic
    if date_from or date_to:
        start = date_from or "19910101"  # arXiv started in 1991
        end = date_to or datetime.now().strftime("%Y%m%d")
        query = f"{topic} AND submittedDate:[{start} TO {end}]"

    # Get sort criterion (default to relevance if invalid)
    sort_criterion = SORT_CRITERIA.get(sort_by, arxiv.SortCriterion.Relevance)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_criterion,
    )

    results = client.results(search)

    # Build the storage path for this topic
    topic_slug = topic.lower().strip().replace(" ", "_")
    topic_dir = os.path.join(RESEARCH_DIR, topic_slug)
    os.makedirs(topic_dir, exist_ok=True)

    metadata_path = os.path.join(topic_dir, "articles.json")

    # Load existing metadata if available
    existing_data = {}
    try:
        with open(metadata_path, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}

    # Process each result from arXiv
    articles = []
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
        articles.append(article_metadata)

    # Save updated metadata
    with open(metadata_path, "w") as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Found {len(articles)} articles for topic '{topic}', saved to {metadata_path}")

    return articles
