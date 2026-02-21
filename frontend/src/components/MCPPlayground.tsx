"use client";

import { useState, useRef, useEffect } from "react";
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

function StepIcon({ type }: { type: string }) {
  if (type === "thinking") return <span className="text-blue-400 text-sm">&#x1f9e0;</span>;
  if (type === "tool_call") return <span className="text-amber-400 text-sm">&#x1f527;</span>;
  if (type === "tool_result") return <span className="text-green-400 text-sm">&#x2705;</span>;
  if (type === "error") return <span className="text-red-400 text-sm">&#x274c;</span>;
  return null;
}

function ToolCallContent({ content }: { content: { name: string; args?: Record<string, unknown> } }) {
  return (
    <div className="font-mono text-sm">
      <span className="text-amber-300 font-semibold">{content.name}</span>
      <span className="text-slate-400">(</span>
      {content.args && Object.entries(content.args).map(([key, val], i) => (
        <span key={key}>
          {i > 0 && <span className="text-slate-400">, </span>}
          <span className="text-slate-400">{key}=</span>
          <span className="text-emerald-300">
            {typeof val === "string" ? `"${val}"` : JSON.stringify(val)}
          </span>
        </span>
      ))}
      <span className="text-slate-400">)</span>
    </div>
  );
}

function ToolResultContent({ content }: { content: { name: string; result?: string } }) {
  const resultStr = content.result || "";
  let parsed = null;
  try {
    parsed = JSON.parse(resultStr);
  } catch {
    // not JSON
  }

  return (
    <div className="text-sm">
      <span className="text-green-400 font-semibold">{content.name}</span>
      <span className="text-slate-400"> returned:</span>
      <pre className="mt-1 text-xs text-slate-300 bg-slate-800/50 rounded p-2 overflow-x-auto max-h-40 overflow-y-auto">
        {parsed ? JSON.stringify(parsed, null, 2) : resultStr}
      </pre>
    </div>
  );
}

export default function MCPPlayground() {
  const [query, setQuery] = useState("");
  const [steps, setSteps] = useState<MCPStep[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stepsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    stepsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps, answer]);

  const handleSubmit = (queryText?: string) => {
    const q = queryText || query;
    if (!q.trim() || isStreaming) return;

    setSteps([]);
    setAnswer(null);
    setError(null);
    setIsStreaming(true);
    setQuery(q);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

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
        // ignore malformed events
      }
    };

    es.onerror = () => {
      es.close();
      setIsStreaming(false);
      if (!answer && steps.length === 0) {
        setError("Connection lost. The server may be starting up -- please try again in a minute.");
      }
    };
  };

  const handleStop = () => {
    eventSourceRef.current?.close();
    setIsStreaming(false);
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
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

        {/* Suggested Queries */}
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
          {/* AI Agent Activity Panel */}
          <div className="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-700 flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${isStreaming ? "bg-green-400 animate-pulse" : "bg-slate-500"}`}
              />
              <h3 className="text-sm font-semibold text-slate-200">
                AI Agent Activity
              </h3>
              {isStreaming && (
                <span className="ml-auto text-xs text-green-400">Live</span>
              )}
            </div>
            <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
              {steps.map((step, i) => (
                <div key={i} className="flex gap-2">
                  <StepIcon type={step.type} />
                  <div className="flex-1 min-w-0">
                    {step.type === "thinking" && (
                      <p className="text-sm text-blue-300 italic">
                        {step.content as string}
                      </p>
                    )}
                    {step.type === "tool_call" && (
                      <ToolCallContent
                        content={
                          step.content as {
                            name: string;
                            args?: Record<string, unknown>;
                          }
                        }
                      />
                    )}
                    {step.type === "tool_result" && (
                      <ToolResultContent
                        content={
                          step.content as {
                            name: string;
                            result?: string;
                          }
                        }
                      />
                    )}
                  </div>
                </div>
              ))}
              {isStreaming && (
                <div className="flex gap-2 items-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                  <span className="text-xs text-slate-400">
                    Agent is working...
                  </span>
                </div>
              )}
              <div ref={stepsEndRef} />
            </div>
          </div>

          {/* Final Response Panel */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100">
              <h3 className="text-sm font-semibold text-gray-700">
                Response
              </h3>
            </div>
            <div className="p-5 max-h-[500px] overflow-y-auto">
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
