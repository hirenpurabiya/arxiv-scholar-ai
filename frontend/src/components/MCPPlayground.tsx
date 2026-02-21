"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Article, MCPStep } from "@/lib/types";
import { getArticleDetails } from "@/lib/api";
import ArticleCard from "./ArticleCard";
import ArticleDetail from "./ArticleDetail";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const SUGGESTED_QUERIES = [
  "Find the latest papers on transformer architecture and summarize the top one",
  "Search for papers about RAG and explain the best one like I'm 10",
  "What are the newest papers on LLM reasoning?",
  "Find papers about diffusion models and give me a summary",
];

function parsePapersFromResult(result: string, queryTopic: string): Article[] {
  try {
    const parsed = JSON.parse(result);
    if (!parsed.papers || !Array.isArray(parsed.papers)) return [];
    return parsed.papers.map(
      (p: { id: string; title: string; authors: string[]; published: string }) => ({
        id: p.id,
        title: p.title,
        authors: p.authors || [],
        published: p.published || "",
        summary: "",
        pdf_url: `https://arxiv.org/pdf/${p.id}`,
        topic: queryTopic,
      })
    );
  } catch {
    return [];
  }
}

function ToolResultCollapsible({
  name,
  result,
}: {
  name: string;
  result: string;
}) {
  const [expanded, setExpanded] = useState(false);

  let summary = "";
  try {
    const parsed = JSON.parse(result);
    if (parsed.count !== undefined) {
      summary = `Found ${parsed.count} paper${parsed.count !== 1 ? "s" : ""}`;
    } else if (parsed.error) {
      summary = parsed.error;
    } else if (parsed.title) {
      summary = parsed.title;
    }
  } catch {
    summary = result.length > 80 ? result.slice(0, 80) + "..." : result;
  }

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 w-full text-left group"
      >
        <svg
          className={`w-3 h-3 text-gray-400 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-sm text-gray-500">
          Result from{" "}
          <span className="text-gray-700 font-medium">{name}</span>
        </span>
        {!expanded && summary && (
          <span className="text-xs text-gray-400 truncate ml-1">
            -- {summary}
          </span>
        )}
      </button>
      {expanded && (
        <pre className="mt-2 ml-5 text-xs text-gray-600 bg-gray-50 rounded-lg p-3 overflow-x-auto max-h-48 overflow-y-auto border border-gray-100">
          {(() => {
            try {
              return JSON.stringify(JSON.parse(result), null, 2);
            } catch {
              return result;
            }
          })()}
        </pre>
      )}
    </div>
  );
}

function ElapsedTimer({ startTime }: { startTime: number }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const interval = setInterval(
      () => setElapsed(Math.floor((Date.now() - startTime) / 1000)),
      1000
    );
    return () => clearInterval(interval);
  }, [startTime]);
  return <span>{elapsed}s</span>;
}

export default function MCPPlayground() {
  const [query, setQuery] = useState("");
  const [steps, setSteps] = useState<MCPStep[]>([]);
  const [papers, setPapers] = useState<Article[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);
  const activityPanelRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollActivityToBottom = useCallback(() => {
    const el = activityPanelRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    scrollActivityToBottom();
  }, [steps, scrollActivityToBottom]);

  const handleSubmit = (queryText?: string) => {
    const q = queryText || query;
    if (!q.trim() || isStreaming) return;

    setSteps([]);
    setPapers([]);
    setSelectedArticle(null);
    setError(null);
    setIsStreaming(true);
    setStartTime(Date.now());
    setQuery(q);

    if (eventSourceRef.current) eventSourceRef.current.close();

    const es = new EventSource(
      `${API_BASE}/api/mcp-query?q=${encodeURIComponent(q.trim())}`
    );
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const step: MCPStep = JSON.parse(event.data);

        if (step.type === "done") {
          es.close();
          setIsStreaming(false);
          return;
        }
        if (step.type === "answer") {
          // We don't display the text answer anymore; papers are shown as cards
          es.close();
          setIsStreaming(false);
          return;
        }
        if (step.type === "error") {
          setError(step.content as string);
          es.close();
          setIsStreaming(false);
          return;
        }

        setSteps((prev) => [...prev, step]);

        if (step.type === "tool_result") {
          const tr = step.content as { name: string; result?: string };
          if (tr.name === "search_arxiv" && tr.result) {
            const found = parsePapersFromResult(tr.result, q);
            if (found.length > 0) setPapers(found);
          }
        }
      } catch {
        // ignore malformed
      }
    };

    es.onerror = () => {
      es.close();
      setIsStreaming(false);
      if (steps.length === 0 && papers.length === 0) {
        setError(
          "Connection lost. The server may be starting up -- please try again in a minute."
        );
      }
    };
  };

  const handleStop = () => {
    eventSourceRef.current?.close();
    setIsStreaming(false);
  };

  const handleSelectArticle = async (article: Article) => {
    try {
      const full = await getArticleDetails(article.id);
      setSelectedArticle(full);
    } catch {
      setSelectedArticle(article);
    }
    setTimeout(() => window.scrollTo({ top: 0, behavior: "smooth" }), 50);
  };

  const handleBack = () => setSelectedArticle(null);

  return (
    <div className="space-y-6 min-w-0">
      {/* Input */}
      {!selectedArticle && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 sm:p-5 min-w-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit();
            }}
            className="flex flex-col sm:flex-row gap-3 min-w-0"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about research papers..."
              className="flex-1 min-w-0 px-4 py-3 rounded-lg border border-gray-200 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={handleStop}
                className="px-6 py-3 rounded-lg bg-red-500 text-white font-medium text-sm hover:bg-red-600 transition-colors"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!query.trim()}
                className="px-6 py-3 rounded-lg bg-blue-600 text-white font-medium text-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Run Agent
              </button>
            )}
          </form>

          {steps.length === 0 && !error && papers.length === 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.map((sq) => (
                <button
                  key={sq}
                  onClick={() => {
                    setQuery(sq);
                    handleSubmit(sq);
                  }}
                  className="px-3 py-1.5 text-xs rounded-full border border-gray-200 text-gray-600 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors"
                  disabled={isStreaming}
                >
                  {sq}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Article Detail View */}
      {selectedArticle && (
        <ArticleDetail article={selectedArticle} onBack={handleBack} />
      )}

      {/* Thinking Panel (full width) */}
      {!selectedArticle && (steps.length > 0 || error) && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col min-w-0">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2 shrink-0">
            <div
              className={`w-2 h-2 rounded-full ${isStreaming ? "bg-green-500 animate-pulse" : "bg-gray-300"}`}
            />
            <h3 className="text-sm font-semibold text-gray-700">
              Thinking
            </h3>
            {isStreaming && startTime && (
              <span className="ml-auto text-xs text-gray-400">
                <ElapsedTimer startTime={startTime} />
              </span>
            )}
          </div>

          <div
            ref={activityPanelRef}
            className="p-4 space-y-4 overflow-y-auto"
            style={{ height: "400px" }}
          >
            {steps.map((step, i) => {
              if (step.type === "thinking") {
                return (
                  <div key={i} className="border-l-2 border-gray-200 pl-3">
                    <p className="text-xs font-medium text-gray-400 mb-1">
                      Thinking
                    </p>
                    <p className="text-sm text-gray-700">
                      {step.content as string}
                    </p>
                  </div>
                );
              }

              if (step.type === "tool_call") {
                const tc = step.content as {
                  name: string;
                  args?: Record<string, unknown>;
                };
                return (
                  <div key={i} className="border-l-2 border-amber-400 pl-3">
                    <p className="text-xs font-medium text-gray-400 mb-1">
                      Called{" "}
                      <span className="text-amber-600 font-semibold">{tc.name}</span>
                    </p>
                    {tc.args && Object.keys(tc.args).length > 0 && (
                      <div className="space-y-0.5">
                        {Object.entries(tc.args).map(([key, val]) => (
                          <p key={key} className="text-sm text-gray-500">
                            <span className="text-gray-400">{key}:</span>{" "}
                            <span className="text-emerald-600">
                              {typeof val === "string"
                                ? `"${val}"`
                                : JSON.stringify(val)}
                            </span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                );
              }

              if (step.type === "tool_result") {
                const tr = step.content as {
                  name: string;
                  result?: string;
                };
                return (
                  <div key={i} className="border-l-2 border-green-400 pl-3">
                    <ToolResultCollapsible
                      name={tr.name}
                      result={tr.result || ""}
                    />
                  </div>
                );
              }

              return null;
            })}

            {isStreaming && (
              <div className="border-l-2 border-blue-400 pl-3">
                <p className="text-xs font-medium text-gray-400 mb-1">
                  Thinking
                </p>
                <span className="inline-block w-2 h-4 bg-gray-300 animate-pulse rounded-sm" />
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Paper Cards */}
      {!selectedArticle && papers.length > 0 && (
        <div className="min-w-0">
          <p className="text-sm text-gray-500 mb-4">
            Found {papers.length} paper{papers.length !== 1 ? "s" : ""}
          </p>
          <div className="flex flex-col gap-4">
            {papers.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onSelect={handleSelectArticle}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
