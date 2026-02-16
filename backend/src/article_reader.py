"""
Article Reader module for ArXiv Scholar AI.
Retrieves stored article metadata by ID across all topic directories.
"""

import json
import os
import logging
from typing import Optional, Dict, Any, List

from .config import RESEARCH_DIR

logger = logging.getLogger(__name__)


def get_article_details(article_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a specific article's metadata by its arXiv ID.
    Searches across all topic directories.

    Args:
        article_id: The arXiv short ID (e.g., "2401.12345v2")

    Returns:
        Article metadata dictionary if found, None otherwise
    """
    if not os.path.exists(RESEARCH_DIR):
        logger.warning(f"Research directory '{RESEARCH_DIR}' does not exist")
        return None

    for topic_folder in os.listdir(RESEARCH_DIR):
        folder_path = os.path.join(RESEARCH_DIR, topic_folder)

        if not os.path.isdir(folder_path):
            continue

        metadata_path = os.path.join(folder_path, "articles.json")

        if not os.path.isfile(metadata_path):
            continue

        try:
            with open(metadata_path, "r") as f:
                articles_data = json.load(f)

                if article_id in articles_data:
                    logger.info(f"Found article '{article_id}' in topic '{topic_folder}'")
                    return articles_data[article_id]

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error reading {metadata_path}: {e}")
            continue

    logger.info(f"Article '{article_id}' not found in any topic directory")
    return None


def list_all_topics() -> List[str]:
    """
    List all topic directories that contain saved articles.

    Returns:
        List of topic names
    """
    if not os.path.exists(RESEARCH_DIR):
        return []

    topics = []
    for item in os.listdir(RESEARCH_DIR):
        item_path = os.path.join(RESEARCH_DIR, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "articles.json")
            if os.path.isfile(metadata_path):
                topics.append(item)

    return sorted(topics)


def get_articles_by_topic(topic_slug: str) -> Dict[str, Any]:
    """
    Get all articles for a specific topic.

    Args:
        topic_slug: The topic directory name (e.g., "transformer_architecture")

    Returns:
        Dictionary of article_id -> article_metadata
    """
    metadata_path = os.path.join(RESEARCH_DIR, topic_slug, "articles.json")

    try:
        with open(metadata_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
