"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { MCPStep } from "@/lib/types";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

const SUGGESTED_QUERIES = [
  "Find the latest papers on transformer architecture and summarize the top one",
  "Search for papers about RAG and explain the best one like I'm 10",
  "What are the newest papers on LLM reasoning?",
  "Find papers about diffusion models and give me a summary",
];

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
          className={`w-3 h-3 text-slate-500 transition-transform ${expanded ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-sm text-slate-400">
          Result from{" "}
          <span className="text-slate-300 font-medium">{name}</span>
        </span>
        {!expanded && summary && (
          <span className="text-xs text-slate-500 truncate ml-1">
            -- {summary}
          </span>
        )}
      </button>
      {expanded && (
        <pre className="mt-2 ml-5 text-xs text-slate-400 bg-slate-800/40 rounded-lg p-3 overflow-x-auto max-h-48 overflow-y-auto">
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
  const [answer, setAnswer] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);
  const activityPanelRef = useRef<HTMLDivElement>(null);
  const responsePanelRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollActivityToBottom = useCallback(() => {
    const el = activityPanelRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    scrollActivityToBottom();
  }, [steps, scrollActivityToBottom]);

  useEffect(() => {
    const el = responsePanelRef.current;
    if (el && answer) el.scrollTop = el.scrollHeight;
  }, [answer]);

  const handleSubmit = (queryText?: string) => {
    const q = queryText || query;
    if (!q.trim() || isStreaming) return;

    setSteps([]);
    setAnswer(null);
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
          setAnswer(step.content as string);
          return;
        }
        if (step.type === "error") {
          setError(step.content as string);
          es.close();
          setIsStreaming(false);
          return;
        }
        setSteps((prev) => [...prev, step]);
      } catch {
        // ignore malformed
      }
    };

    es.onerror = () => {
      es.close();
      setIsStreaming(false);
      if (!answer && steps.length === 0) {
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

  return (
    <div className="space-y-6">
      {/* Input */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="flex gap-3"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about research papers..."
            className="flex-1 px-4 py-3 rounded-lg border border-gray-200 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
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

        {steps.length === 0 && !answer && !error && (
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

      {/* Two-Panel Layout */}
      {(steps.length > 0 || answer || error) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Agent Activity */}
          <div className="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-slate-700 flex items-center gap-2 shrink-0">
              <div
                className={`w-2 h-2 rounded-full ${isStreaming ? "bg-green-400 animate-pulse" : "bg-slate-500"}`}
              />
              <h3 className="text-sm font-semibold text-slate-200">
                Agent Activity
              </h3>
              {isStreaming && startTime && (
                <span className="ml-auto text-xs text-slate-400">
                  <ElapsedTimer startTime={startTime} />
                </span>
              )}
            </div>

            <div
              ref={activityPanelRef}
              className="p-4 space-y-4 overflow-y-auto"
              style={{ maxHeight: "500px" }}
            >
              {steps.map((step, i) => {
                if (step.type === "thinking") {
                  return (
                    <div
                      key={i}
                      className="border-l-2 border-slate-600 pl-3"
                    >
                      <p className="text-xs font-medium text-slate-500 mb-1">
                        Thinking
                      </p>
                      <p className="text-sm text-slate-300">
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
                    <div key={i} className="border-l-2 border-amber-500/50 pl-3">
                      <p className="text-xs font-medium text-slate-500 mb-1">
                        Called{" "}
                        <span className="text-amber-400">{tc.name}</span>
                      </p>
                      {tc.args && Object.keys(tc.args).length > 0 && (
                        <div className="space-y-0.5">
                          {Object.entries(tc.args).map(([key, val]) => (
                            <p
                              key={key}
                              className="text-sm text-slate-400"
                            >
                              <span className="text-slate-500">{key}:</span>{" "}
                              <span className="text-emerald-400">
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
                    <div key={i} className="border-l-2 border-green-500/50 pl-3">
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
                <div className="border-l-2 border-blue-500/50 pl-3">
                  <p className="text-xs font-medium text-slate-500 mb-1">
                    Thinking
                  </p>
                  <span className="inline-block w-2 h-4 bg-slate-400 animate-pulse rounded-sm" />
                </div>
              )}
            </div>
          </div>

          {/* Response */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-gray-100 shrink-0">
              <h3 className="text-sm font-semibold text-gray-700">Response</h3>
            </div>
            <div
              ref={responsePanelRef}
              className="p-5 overflow-y-auto"
              style={{ maxHeight: "500px" }}
            >
              {error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              ) : answer ? (
                <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                  {answer}
                </div>
              ) : isStreaming ? (
                <div className="flex items-center gap-3 text-gray-400">
                  <div className="w-5 h-5 border-2 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
                  <span className="text-sm">
                    Waiting for the agent to finish...
                  </span>
                </div>
              ) : (
                <p className="text-sm text-gray-400">
                  The agent&apos;s response will appear here.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
