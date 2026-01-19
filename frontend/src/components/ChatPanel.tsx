"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, FileText, User, Loader2 } from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/lib/store";
import api from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: { file: string; lines?: string }[];
}

const welcomeMessage: Message = {
  id: "welcome",
  role: "assistant",
  content: `Welcome to CodeAtlas! 👋

I can help you understand and navigate your codebase. Try asking me:

• "How does this project work?"
• "Where is [function name] defined?"
• "What files import [module]?"
• "Explain the architecture"

Import a project to get started, or explore the demo!`,
  citations: [],
};

export function ChatPanel() {
  const { currentSnapshot, chatSessionId, setChatSessionId, setSelectedFile } = useAppStore();
  const [messages, setMessages] = useState<Message[]>([welcomeMessage]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      if (currentSnapshot) {
        // Real API call
        const response = await api.chat(currentSnapshot.id, input, chatSessionId || undefined);
        setChatSessionId(response.session_id);

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: response.message.content,
          citations: response.message.citations,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        // Demo response
        setTimeout(() => {
          const demoResponse: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: `I'd love to help you with "${input}"!

To analyze your codebase, please import a project first using the **Import** button in the sidebar.

Once imported, I can:
• Answer questions about your code
• Explain how components work together
• Help you find specific functions and files
• Suggest improvements and refactors`,
            citations: [],
          };
          setMessages((prev) => [...prev, demoResponse]);
          setIsLoading(false);
        }, 1000);
        return;
      }
    } catch (err) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : "Unknown error"}. Please try again.`,
        citations: [],
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCitationClick = (citation: { file: string; lines?: string }) => {
    setSelectedFile(citation.file);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={clsx(
              "animate-slide-up",
              msg.role === "user" ? "flex justify-end" : ""
            )}
          >
            <div
              className={clsx(
                "max-w-[85%] rounded-xl p-4",
                msg.role === "user"
                  ? "bg-arb-accent/20 border border-arb-accent/30 text-arb-text"
                  : "bg-arb-surface border border-arb-border"
              )}
            >
              {/* Role indicator */}
              <div className="flex items-center gap-2 mb-2">
                {msg.role === "assistant" ? (
                  <div className="w-5 h-5 rounded-full bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center">
                    <Sparkles className="w-3 h-3 text-white" />
                  </div>
                ) : (
                  <div className="w-5 h-5 rounded-full bg-arb-border flex items-center justify-center">
                    <User className="w-3 h-3 text-arb-text-dim" />
                  </div>
                )}
                <span className="text-xs font-medium text-arb-text-dim uppercase">
                  {msg.role === "assistant" ? "CodeAtlas" : "You"}
                </span>
              </div>

              {/* Content */}
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-arb-border/50">
                  <div className="text-xs text-arb-text-muted mb-2">
                    References:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((cite, i) => (
                      <button
                        key={i}
                        onClick={() => handleCitationClick(cite)}
                        className="flex items-center gap-1.5 px-2 py-1 rounded bg-arb-bg/50 border border-arb-border text-xs hover:border-arb-accent/50 transition-colors"
                      >
                        <FileText className="w-3 h-3 text-arb-accent" />
                        <span className="text-arb-text-dim">{cite.file}</span>
                        {cite.lines && (
                          <span className="text-arb-text-muted">
                            :{cite.lines}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex items-center gap-2 text-arb-text-dim animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-arb-border bg-arb-panel">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                currentSnapshot
                  ? "Ask about the codebase..."
                  : "Import a project to start chatting..."
              }
              rows={1}
              disabled={isLoading}
              className="w-full resize-none px-4 py-3 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all disabled:opacity-50"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-3 rounded-xl bg-arb-accent hover:bg-arb-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-glow"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
