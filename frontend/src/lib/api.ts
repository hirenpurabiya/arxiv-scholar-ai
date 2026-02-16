/**
 * API client functions for communicating with the ArXiv Scholar AI backend.
 */

import { SearchResponse, Article, SummaryResponse, TopicsResponse } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/**
 * Search for articles on arXiv by topic.
 */
export async function searchArticles(
  topic: string,
  maxResults: number = 5
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    topic,
    max_results: String(maxResults),
  });

  const response = await fetch(`${API_BASE}/api/search?${params}`);

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get details for a specific article by its arXiv ID.
 */
export async function getArticleDetails(articleId: string): Promise<Article> {
  const response = await fetch(`${API_BASE}/api/article/${articleId}`);

  if (!response.ok) {
    throw new Error(`Article not found: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Generate a free summary by extracting key sentences.
 */
export async function summarizeArticle(
  articleId: string
): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE}/api/summarize/${articleId}`);

  if (!response.ok) {
    throw new Error(`Summarization failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Explain a paper like I'm 10 -- simple breakdown.
 */
export async function explainLikeTen(
  articleId: string
): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE}/api/eli10/${articleId}`);

  if (!response.ok) {
    throw new Error(`Explanation failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * List all topics that have been searched.
 */
export async function getTopics(): Promise<TopicsResponse> {
  const response = await fetch(`${API_BASE}/api/topics`);

  if (!response.ok) {
    throw new Error(`Failed to fetch topics: ${response.statusText}`);
  }

  return response.json();
}
