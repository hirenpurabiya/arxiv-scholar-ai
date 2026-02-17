"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import SearchBar from "@/components/SearchBar";
import ArticleCard from "@/components/ArticleCard";
import ArticleDetail from "@/components/ArticleDetail";
import { searchArticles } from "@/lib/api";
import { Article, SearchFilters, SortOption, DatePreset } from "@/lib/types";

const DEFAULT_FILTERS: SearchFilters = {
  sortBy: "relevance",
  datePreset: "all",
};

function HomeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [articles, setArticles] = useState<Article[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchedTopic, setSearchedTopic] = useState<string>("");
  const [copiedLink, setCopiedLink] = useState(false);

  // Parse filters from URL on mount
  const getFiltersFromUrl = useCallback((): SearchFilters => {
    const sortBy = (searchParams.get("sort") as SortOption) || "relevance";
    const datePreset = (searchParams.get("date") as DatePreset) || "all";
    const dateFrom = searchParams.get("from") || undefined;
    const dateTo = searchParams.get("to") || undefined;

    return {
      sortBy,
      datePreset: dateFrom || dateTo ? "custom" : datePreset,
      dateFrom,
      dateTo,
    };
  }, [searchParams]);

  const initialTopic = searchParams.get("q") || "";
  const initialFilters = getFiltersFromUrl();

  // Auto-search if URL has query params
  useEffect(() => {
    if (initialTopic) {
      handleSearch(initialTopic, 5, initialFilters);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = async (
    topic: string,
    maxResults: number,
    filters: SearchFilters
  ) => {
    setIsLoading(true);
    setError(null);
    setSelectedArticle(null);
    setSearchedTopic(topic);

    // Update URL with search params
    updateUrl(topic, filters);

    try {
      const result = await searchArticles(topic, maxResults, filters);
      setArticles(result.articles);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred"
      );
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const updateUrl = (topic: string, filters: SearchFilters) => {
    const params = new URLSearchParams();
    params.set("q", topic);

    if (filters.sortBy !== "relevance") {
      params.set("sort", filters.sortBy);
    }

    if (filters.datePreset === "custom") {
      if (filters.dateFrom) params.set("from", filters.dateFrom);
      if (filters.dateTo) params.set("to", filters.dateTo);
    } else if (filters.datePreset !== "all") {
      params.set("date", filters.datePreset);
    }

    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const handleShare = (topic: string, filters: SearchFilters) => {
    const params = new URLSearchParams();
    params.set("q", topic);

    if (filters.sortBy !== "relevance") {
      params.set("sort", filters.sortBy);
    }

    if (filters.datePreset === "custom") {
      if (filters.dateFrom) params.set("from", filters.dateFrom);
      if (filters.dateTo) params.set("to", filters.dateTo);
    } else if (filters.datePreset !== "all") {
      params.set("date", filters.datePreset);
    }

    const shareUrl = `${window.location.origin}?${params.toString()}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleSelectArticle = (article: Article) => {
    setSelectedArticle(article);
  };

  const handleBack = () => {
    setSelectedArticle(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AS</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                ArXiv Scholar AI
              </h1>
              <p className="text-xs text-gray-500">
                AI-powered research paper discovery
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Copied Link Toast */}
      {copiedLink && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-fade-in">
          Link copied to clipboard!
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-10">
        {/* Hero / Search Section */}
        {!selectedArticle && (
          <div className="text-center mb-10">
            {articles.length === 0 && !error && !isLoading && (
              <>
                <h2 className="text-4xl font-bold text-gray-900 mb-3">
                  Discover Research Papers
                </h2>
                <p className="text-lg text-gray-500 mb-8 max-w-xl mx-auto">
                  Search arXiv for academic papers on any topic. Get AI-powered
                  summaries to quickly understand what matters.
                </p>
              </>
            )}
            <SearchBar
              onSearch={handleSearch}
              isLoading={isLoading}
              initialTopic={initialTopic}
              initialFilters={initialFilters}
              onShare={handleShare}
            />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-3xl mx-auto mt-6">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-20">
            <div className="inline-block w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-500">
              Searching arXiv for &quot;{searchedTopic}&quot;...
            </p>
          </div>
        )}

        {/* Article Detail View */}
        {selectedArticle && (
          <ArticleDetail article={selectedArticle} onBack={handleBack} />
        )}

        {/* Results List */}
        {!selectedArticle && !isLoading && articles.length > 0 && (
          <div className="max-w-3xl mx-auto">
            <p className="text-sm text-gray-500 mb-4">
              Found {articles.length} articles for &quot;{searchedTopic}&quot;
            </p>
            <div className="flex flex-col gap-4">
              {articles.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onSelect={handleSelectArticle}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 mt-20">
        <div className="max-w-6xl mx-auto px-6 py-6 text-center">
          <p className="text-sm text-gray-400">
            ArXiv Scholar AI &mdash; Built with Next.js, FastAPI, and Claude
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center">
        <div className="inline-block w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
