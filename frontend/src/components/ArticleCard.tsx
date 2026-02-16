"use client";

import { Article } from "@/lib/types";

interface ArticleCardProps {
  article: Article;
  onSelect: (article: Article) => void;
}

export default function ArticleCard({ article, onSelect }: ArticleCardProps) {
  return (
    <div
      onClick={() => onSelect(article)}
      className="bg-white rounded-xl border border-gray-200 p-6 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 leading-snug mb-2 line-clamp-2">
            {article.title}
          </h3>
          <p className="text-sm text-gray-500 mb-3">
            {article.authors.slice(0, 3).join(", ")}
            {article.authors.length > 3 && ` + ${article.authors.length - 3} more`}
          </p>
          <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">
            {article.summary}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
        <span className="text-xs font-medium text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
          {article.id}
        </span>
        <span className="text-xs text-gray-400">
          Published: {article.published}
        </span>
        <a
          href={article.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="ml-auto text-xs font-medium text-red-600 hover:text-red-700 bg-red-50 px-3 py-1 rounded-full hover:bg-red-100 transition-colors"
        >
          PDF
        </a>
      </div>
    </div>
  );
}
