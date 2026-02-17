/**
 * TypeScript type definitions for ArXiv Scholar AI.
 * Mirrors the backend API response models.
 */

export interface Article {
  id: string;
  title: string;
  authors: string[];
  summary: string;
  pdf_url: string;
  published: string;
  topic: string;
}

export interface SearchResponse {
  topic: string;
  count: number;
  articles: Article[];
}

export interface SummaryResponse {
  article_id: string;
  title: string;
  ai_summary: string | null;
}

export interface TopicsResponse {
  topics: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export type AIProvider = "grok" | "gemini" | "claude";

export interface ChatRequest {
  article_id: string;
  message: string;
  history: ChatMessage[];
  provider: AIProvider;
}

export interface ChatResponse {
  response: string;
  provider: string;
  error_type?: string;
  suggestion?: string;
}
