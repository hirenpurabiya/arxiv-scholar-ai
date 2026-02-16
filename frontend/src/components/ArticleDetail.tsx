"use client";

import { useState } from "react";
import { Article } from "@/lib/types";
import { summarizeArticle } from "@/lib/api";

interface ArticleDetailProps {
  article: Article;
  onBack: () => void;
}

export default function ArticleDetail({ article, onBack }: ArticleDetailProps) {
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const handleSummarize = async () => {
    setIsLoadingSummary(true);
    setSummaryError(null);
    try {
      const result = await summarizeArticle(article.id);
      setAiSummary(result.ai_summary);
    } catch (err) {
      setSummaryError(
        err instanceof Error ? err.message : "Failed to generate summary"
      );
    } finally {
      setIsLoadingSummary(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <button
        onClick={onBack}
        className="mb-6 text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 transition-colors"
      >
        <span>&larr;</span> Back to results
      </button>

      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        <div className="flex items-start justify-between gap-4 mb-4">
          <span className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
            {article.id}
          </span>
          <span className="text-sm text-gray-400">
            Published: {article.published}
          </span>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-4 leading-tight">
          {article.title}
        </h1>

        <div className="flex flex-wrap gap-2 mb-6">
          {article.authors.map((author, i) => (
            <span
              key={i}
              className="text-sm bg-gray-100 text-gray-600 px-3 py-1 rounded-full"
            >
              {author}
            </span>
          ))}
        </div>

        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Abstract
          </h2>
          <p className="text-gray-700 leading-relaxed whitespace-pre-line">
            {article.summary}
          </p>
        </div>

        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            AI Summary
          </h2>
          {aiSummary ? (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
              <p className="text-gray-800 leading-relaxed">{aiSummary}</p>
            </div>
          ) : summaryError ? (
            <div className="bg-red-50 rounded-xl p-5 border border-red-100">
              <p className="text-red-600 text-sm">{summaryError}</p>
            </div>
          ) : (
            <button
              onClick={handleSummarize}
              disabled={isLoadingSummary}
              className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              {isLoadingSummary
                ? "Generating summary with Claude..."
                : "Generate AI Summary"}
            </button>
          )}
        </div>

        <div className="flex gap-3 pt-4 border-t border-gray-100">
          <a
            href={article.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 bg-red-600 text-white font-medium rounded-xl hover:bg-red-700 transition-colors shadow-sm"
          >
            View PDF
          </a>
          <a
            href={`https://arxiv.org/abs/${article.id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-colors"
          >
            View on arXiv
          </a>
        </div>
      </div>
    </div>
  );
}
