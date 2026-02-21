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

export interface ChatRequest {
  article_id: string;
  message: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  response: string;
  provider: string;
  error_type?: string;
  suggestion?: string;
}

// MCP Agent reasoning step types
export type MCPStepType = "thinking" | "tool_call" | "tool_result" | "answer" | "error" | "done";

export interface MCPStep {
  type: MCPStepType;
  content: string | { name: string; args?: Record<string, unknown>; result?: string };
}

// Search filter types
export type SortOption = "relevance" | "date" | "updated";
export type DatePreset = "all" | "week" | "month" | "year" | "custom";

export interface SearchFilters {
  sortBy: SortOption;
  datePreset: DatePreset;
  dateFrom?: string;  // YYYYMMDD format
  dateTo?: string;    // YYYYMMDD format
}
