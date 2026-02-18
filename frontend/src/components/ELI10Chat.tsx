"use client";

import { useState, useRef, useEffect } from "react";
import { ChatMessage } from "@/lib/types";
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


export default function ELI10Chat({ articleId, articleTitle }: ELI10ChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<string | null>(null);
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
        history.slice(0, -1)
      );

      // Check if there was an error
      if (result.error_type) {
        setError(result.response);
        setSuggestion("Please wait a moment and try again.");
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


  const showSuggestions = messages.length === 1;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
      {/* Header */}
      <div className="bg-gray-800 px-5 py-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">💬</span>
          <div>
            <h3 className="text-white font-semibold text-sm">
              Explain Like I&apos;m 10
            </h3>
            <p className="text-gray-300 text-xs truncate max-w-[250px]">
              {articleTitle}
            </p>
          </div>
        </div>
      </div>


      {/* Messages */}
      <div className="h-96 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-gray-800 text-white rounded-br-md"
                  : "bg-gray-50 text-gray-800 border border-gray-200 rounded-bl-md shadow-sm"
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
                className="text-xs bg-white text-gray-700 border border-gray-200 px-3 py-1.5 rounded-full hover:bg-gray-100 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-50 text-gray-500 border border-gray-200 px-4 py-2.5 rounded-2xl rounded-bl-md shadow-sm text-sm">
              <span className="inline-flex gap-1">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
              </span>
              {" "}Thinking...
            </div>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex justify-start">
            <div className="bg-red-50 text-red-600 border border-red-100 px-4 py-2.5 rounded-2xl rounded-bl-md text-sm">
              <p>{error}</p>
              {suggestion && <p className="mt-1 text-xs text-red-500">{suggestion}</p>}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 bg-white p-3 flex gap-2"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything about this paper..."
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent disabled:opacity-50 placeholder-gray-400"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2.5 bg-gray-800 text-white font-medium rounded-xl hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
        >
          Send
        </button>
      </form>
    </div>
  );
}
