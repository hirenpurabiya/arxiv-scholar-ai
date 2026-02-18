/**
 * API client functions for communicating with the ArXiv Scholar AI backend.
 */

import { SearchResponse, Article, SummaryResponse, TopicsResponse, ChatMessage, ChatResponse, SearchFilters } from "./types";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 3000;

async function fetchWithRetry(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetch(url, options);
      if (response.ok || (response.status !== 500 && response.status !== 502 && response.status !== 503 && response.status !== 504)) {
        return response;
      }
      lastError = new Error(`Server error (${response.status})`);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error("Network error");
    }

    if (attempt < MAX_RETRIES) {
      await new Promise((r) => setTimeout(r, RETRY_DELAY_MS * (attempt + 1)));
    }
  }

  throw lastError || new Error("Request failed after retries");
}

/**
 * Search for articles on arXiv by topic.
 * Supports sorting and date filtering.
 * Retries automatically on server errors (cold start).
 */
export async function searchArticles(
  topic: string,
  maxResults: number = 5,
  filters?: SearchFilters
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    topic,
    max_results: String(maxResults),
  });

  if (filters) {
    params.set("sort_by", filters.sortBy);
    if (filters.dateFrom) {
      params.set("date_from", filters.dateFrom);
    }
    if (filters.dateTo) {
      params.set("date_to", filters.dateTo);
    }
  }

  const response = await fetchWithRetry(`${API_BASE}/api/search?${params}`);

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error("Too many searches. Please wait a minute and try again.");
    }
    throw new Error("Search didn't work this time. Please try again in a moment.");
  }

  return response.json();
}

/**
 * Get details for a specific article by its arXiv ID.
 */
export async function getArticleDetails(articleId: string): Promise<Article> {
  const response = await fetchWithRetry(`${API_BASE}/api/article/${articleId}`);

  if (!response.ok) {
    throw new Error("Couldn't load this article. Please try again.");
  }

  return response.json();
}

/**
 * Generate a free summary by extracting key sentences.
 */
export async function summarizeArticle(
  articleId: string
): Promise<SummaryResponse> {
  const response = await fetchWithRetry(`${API_BASE}/api/summarize/${articleId}`);

  if (!response.ok) {
    throw new Error("Couldn't generate summary. Please try again.");
  }

  return response.json();
}

/**
 * Explain a paper like I'm 10 -- simple breakdown.
 */
export async function explainLikeTen(
  articleId: string
): Promise<SummaryResponse> {
  const response = await fetchWithRetry(`${API_BASE}/api/eli10/${articleId}`);

  if (!response.ok) {
    throw new Error("Couldn't generate explanation. Please try again.");
  }

  return response.json();
}

/**
 * Chat about a paper -- Explain Like I'm 10 interactive chatbot.
 * Powered by Google Gemini (free).
 */
export async function chatWithArticle(
  articleId: string,
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      article_id: articleId,
      message,
      history,
    }),
  });

  if (!response.ok) {
    if (response.status === 429) {
      throw new Error("You're sending messages too fast! Please wait about 60 seconds and try again.");
    }
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || `Something went wrong. Please try again.`);
  }

  return response.json();
}

/**
 * List all topics that have been searched.
 */
export async function getTopics(): Promise<TopicsResponse> {
  const response = await fetchWithRetry(`${API_BASE}/api/topics`);

  if (!response.ok) {
    throw new Error("Couldn't load topics. Please try again.");
  }

  return response.json();
}
