"use client";

import { useState, useEffect } from "react";
import { SearchFilters } from "@/lib/types";
import SearchFiltersComponent from "./SearchFilters";

interface SearchBarProps {
  onSearch: (topic: string, maxResults: number, filters: SearchFilters) => void;
  isLoading: boolean;
  initialTopic?: string;
  initialFilters?: SearchFilters;
  onShare: (topic: string, filters: SearchFilters) => void;
}

const DEFAULT_FILTERS: SearchFilters = {
  sortBy: "relevance",
  datePreset: "all",
};

export default function SearchBar({
  onSearch,
  isLoading,
  initialTopic = "",
  initialFilters = DEFAULT_FILTERS,
  onShare,
}: SearchBarProps) {
  const [topic, setTopic] = useState(initialTopic);
  const [maxResults, setMaxResults] = useState(5);
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [hasSearched, setHasSearched] = useState(false);

  // Update topic if initial value changes (from URL params)
  useEffect(() => {
    if (initialTopic) {
      setTopic(initialTopic);
    }
  }, [initialTopic]);

  // Update filters if initial values change (from URL params)
  useEffect(() => {
    if (initialFilters) {
      setFilters(initialFilters);
    }
  }, [initialFilters]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim()) {
      setHasSearched(true);
      onSearch(topic.trim(), maxResults, filters);
    }
  };

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters);
    // Auto-search when filters change (only if we've already searched)
    if (hasSearched && topic.trim()) {
      onSearch(topic.trim(), maxResults, newFilters);
    }
  };

  const handleShare = () => {
    if (topic.trim()) {
      onShare(topic.trim(), filters);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col sm:flex-row gap-3">
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
      </form>

      {/* Filters - always visible */}
      <SearchFiltersComponent
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onShare={handleShare}
      />
    </div>
  );
}
