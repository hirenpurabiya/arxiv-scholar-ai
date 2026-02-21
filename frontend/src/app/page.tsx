"use client";

import MCPPlayground from "@/components/MCPPlayground";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white overflow-x-hidden">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="w-full max-w-full mx-auto px-4 sm:px-6 lg:px-12 xl:px-20 py-4">
          <div className="flex items-center gap-3">
            <a
              href="https://hirenpurabiya.github.io/ai-portfolio/projects/arxiv-scholar-ai/"
              className="text-sm text-gray-400 hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              <span>&larr;</span>
              <span>Portfolio</span>
            </a>
            <div className="h-6 w-px bg-gray-200" />
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

      {/* Main Content */}
      <main className="w-full max-w-full mx-auto px-4 sm:px-6 lg:px-12 xl:px-20 py-10 min-w-0">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Discover Research Papers
          </h2>
          <p className="text-gray-500 max-w-2xl">
            Search arXiv for academic papers on any topic. Get AI-powered
            summaries to quickly understand what matters.
          </p>
        </div>

        <MCPPlayground />

        {/* How It Works */}
        <div className="mt-12 border-t border-gray-100 pt-10">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            How It Works
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              {
                step: "1",
                title: "You Ask",
                desc: "Type any question about research papers in natural language.",
              },
              {
                step: "2",
                title: "AI Decides",
                desc: "Gemini analyzes your query and picks which MCP tools to use.",
              },
              {
                step: "3",
                title: "Tools Execute",
                desc: "search_arxiv, summarize_paper, explain_paper, and more run in real-time.",
              },
              {
                step: "4",
                title: "Answer Composed",
                desc: "The AI reads the tool results and writes a comprehensive answer.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="relative bg-white rounded-xl border border-gray-100 p-5"
              >
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm mb-3">
                  {item.step}
                </div>
                <h4 className="font-semibold text-gray-900 mb-1">
                  {item.title}
                </h4>
                <p className="text-sm text-gray-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Architecture Note */}
        <div className="mt-8 bg-slate-50 border border-slate-200 rounded-xl p-5">
          <h4 className="text-sm font-semibold text-slate-700 mb-2">
            Architecture
          </h4>
          <p className="text-sm text-slate-600">
            This demo uses the{" "}
            <span className="font-semibold">Model Context Protocol (MCP)</span>{" "}
            pattern: Gemini acts as the AI reasoning engine, MCP tool
            declarations describe what the backend can do, and the agentic loop
            handles tool execution and multi-turn reasoning. Responses stream via
            Server-Sent Events (SSE) for real-time display.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 mt-20">
        <div className="w-full max-w-full mx-auto px-4 sm:px-6 lg:px-12 xl:px-20 py-6 text-center">
          <p className="text-sm text-gray-400">ArXiv Scholar AI</p>
        </div>
      </footer>
    </div>
  );
}
