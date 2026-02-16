"use client";

import { useState } from "react";

interface SearchBarProps {
  onSearch: (topic: string, maxResults: number) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [topic, setTopic] = useState("");
  const [maxResults, setMaxResults] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      onSearch(topic.trim(), maxResults);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="flex flex-col gap-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Search for research papers... (e.g., transformer architecture)"
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm text-lg"
            disabled={isLoading}
          />
          <select
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            className="px-4 py-3 rounded-xl border border-gray-200 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            disabled={isLoading}
          >
            {[3, 5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>
                {n} results
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={isLoading || !topic.trim()}
            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {isLoading ? "Searching..." : "Search"}
          </button>
        </div>
      </div>
    </form>
  );
}
