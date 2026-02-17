"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage, AIProvider } from "@/lib/types";
import { chatWithArticle } from "@/lib/api";

interface ELI10ChatProps {
  articleId: string;
  articleTitle: string;
}

const GREETING: ChatMessage = {
  role: "assistant",
  content:
    "Hi! I read this paper and I'm ready to explain it in simple words. Ask me anything! For example: \"What does this paper do?\" or \"Why does this matter?\"",
};

const SUGGESTED_QUESTIONS = [
  "What does this paper do?",
  "Why does this matter?",
  "How does it work?",
  "What problem does it solve?",
];

const PROVIDERS: { id: AIProvider; name: string }[] = [
  { id: "grok", name: "xAI Grok" },
  { id: "gemini", name: "Google Gemini" },
  { id: "claude", name: "Anthropic Claude" },
];

export default function ELI10Chat({ articleId, articleTitle }: ELI10ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<AIProvider | null>(null);
  const [provider, setProvider] = useState<AIProvider>("grok");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: text.trim() };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setError(null);
    setSuggestion(null);
    setIsLoading(true);

    try {
      const history = updatedMessages
        .filter((m) => m !== GREETING)
        .map((m) => ({ role: m.role, content: m.content }));

      const result = await chatWithArticle(
        articleId,
        text.trim(),
        history.slice(0, -1),
        provider
      );

      // Check if the provider failed
      if (result.error_type) {
        setError(result.response);
        // Suggest a different provider
        if (provider === "grok") {
          setSuggestion("gemini");
        } else if (provider === "gemini") {
          setSuggestion("grok");
        } else {
          setSuggestion("gemini");
        }
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: result.response },
        ]);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong. Try again!"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSuggestion = (question: string) => {
    sendMessage(question);
  };

  const handleSwitchProvider = (newProvider: AIProvider) => {
    setProvider(newProvider);
    setError(null);
    setSuggestion(null);
  };

  const showSuggestions = messages.length === 1;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border border-amber-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">💬</span>
          <div>
            <h3 className="text-white font-semibold text-sm">
              Explain Like I&apos;m 10
            </h3>
            <p className="text-amber-100 text-xs truncate max-w-[180px]">
              {articleTitle}
            </p>
          </div>
        </div>
        {/* Provider selector */}
        <select
          value={provider}
          onChange={(e) => handleSwitchProvider(e.target.value as AIProvider)}
          className="text-xs bg-white/20 text-white border border-white/30 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-white/50 cursor-pointer"
        >
          {PROVIDERS.map((p) => (
            <option key={p.id} value={p.id} className="text-gray-800">
              {p.name}
            </option>
          ))}
        </select>
      </div>


      {/* Messages */}
      <div className="h-72 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-amber-500 text-white rounded-br-md"
                  : "bg-white text-gray-800 border border-amber-100 rounded-bl-md shadow-sm"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Suggested questions */}
        {showSuggestions && (
          <div className="flex flex-wrap gap-2 pt-1">
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSuggestion(q)}
                className="text-xs bg-white text-amber-700 border border-amber-200 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-500 border border-amber-100 px-4 py-2.5 rounded-2xl rounded-bl-md shadow-sm text-sm">
              <span className="inline-flex gap-1">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
              </span>
              {" "}Thinking...
            </div>
          </div>
        )}

        {/* Error with switch suggestion */}
        {error && (
          <div className="flex justify-start">
            <div className="bg-red-50 text-red-600 border border-red-100 px-4 py-2.5 rounded-2xl rounded-bl-md text-sm">
              <p>{error}</p>
              {suggestion && (
                <button
                  onClick={() => handleSwitchProvider(suggestion)}
                  className="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded-full transition-colors"
                >
                  Switch to {PROVIDERS.find((p) => p.id === suggestion)?.name}
                </button>
              )}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-amber-200 bg-white p-3 flex gap-2"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything about this paper..."
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent disabled:opacity-50 placeholder-gray-400"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium rounded-xl hover:from-amber-600 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
        >
          Send
        </button>
      </form>
    </div>
  );
}
