"use client";

import { useState } from "react";
import { SearchFilters, SortOption, DatePreset } from "@/lib/types";

interface SearchFiltersProps {
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
}

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "relevance", label: "Most Relevant" },
  { value: "date", label: "Newest First" },
  { value: "updated", label: "Recently Updated" },
];

const DATE_PRESETS: { value: DatePreset; label: string }[] = [
  { value: "all", label: "All Time" },
  { value: "week", label: "Last Week" },
  { value: "month", label: "Last Month" },
  { value: "year", label: "Last Year" },
  { value: "custom", label: "Custom" },
];

/**
 * Calculate date range based on preset.
 * Returns dates in YYYYMMDD format for the API.
 */
function getDateRangeFromPreset(preset: DatePreset): { dateFrom?: string; dateTo?: string } {
  if (preset === "all" || preset === "custom") {
    return {};
  }

  const now = new Date();
  const today = formatDate(now);
  let fromDate: Date;

  switch (preset) {
    case "week":
      fromDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case "month":
      fromDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
      break;
    case "year":
      fromDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      break;
    default:
      return {};
  }

  return {
    dateFrom: formatDate(fromDate),
    dateTo: today,
  };
}

/**
 * Format a Date object to YYYYMMDD string.
 */
function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * Format YYYYMMDD to YYYY-MM-DD for input[type=date].
 */
function toInputDate(yyyymmdd: string | undefined): string {
  if (!yyyymmdd || yyyymmdd.length !== 8) return "";
  return `${yyyymmdd.slice(0, 4)}-${yyyymmdd.slice(4, 6)}-${yyyymmdd.slice(6, 8)}`;
}

/**
 * Format YYYY-MM-DD from input to YYYYMMDD for API.
 */
function fromInputDate(inputDate: string): string {
  return inputDate.replace(/-/g, "");
}

export default function SearchFiltersComponent({
  filters,
  onFiltersChange,
}: SearchFiltersProps) {
  const [showCustomDates, setShowCustomDates] = useState(filters.datePreset === "custom");

  const handleSortChange = (sortBy: SortOption) => {
    onFiltersChange({ ...filters, sortBy });
  };

  const handlePresetChange = (preset: DatePreset) => {
    const dateRange = getDateRangeFromPreset(preset);
    setShowCustomDates(preset === "custom");
    
    onFiltersChange({
      ...filters,
      datePreset: preset,
      dateFrom: dateRange.dateFrom,
      dateTo: dateRange.dateTo,
    });
  };

  const handleCustomDateChange = (field: "dateFrom" | "dateTo", value: string) => {
    onFiltersChange({
      ...filters,
      [field]: value ? fromInputDate(value) : undefined,
    });
  };

  return (
    <div className="space-y-3">
      {/* Sort and Date Presets Row */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Sort Dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 font-medium">Sort:</label>
          <select
            value={filters.sortBy}
            onChange={(e) => handleSortChange(e.target.value as SortOption)}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Divider */}
        <div className="h-6 w-px bg-gray-300 hidden sm:block" />

        {/* Date Presets */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 font-medium">Date:</label>
          <div className="flex flex-wrap gap-1">
            {DATE_PRESETS.map((preset) => (
              <button
                key={preset.value}
                onClick={() => handlePresetChange(preset.value)}
                className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                  filters.datePreset === preset.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Custom Date Range (shown when "Custom" is selected) */}
      {showCustomDates && (
        <div className="flex flex-wrap items-center gap-3 pl-0 sm:pl-16">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">From:</label>
            <input
              type="date"
              value={toInputDate(filters.dateFrom)}
              onChange={(e) => handleCustomDateChange("dateFrom", e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">To:</label>
            <input
              type="date"
              value={toInputDate(filters.dateTo)}
              onChange={(e) => handleCustomDateChange("dateTo", e.target.value)}
              className="text-sm border border-gray-300 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}
    </div>
  );
}
