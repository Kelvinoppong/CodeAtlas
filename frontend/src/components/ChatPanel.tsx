"use client";

import { useState } from "react";
import { Send, Sparkles, Code, FileText, User } from "lucide-react";
import clsx from "clsx";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: { file: string; lines?: string }[];
}

const demoMessages: Message[] = [
  {
    id: "1",
    role: "user",
    content: "My friend sent me this really cool project! How does it work? 🎮",
  },
  {
    id: "2",
    role: "assistant",
    content: `It looks like you're talking about a Minesweeper game! It's a classic game of logic and deduction. Here's a breakdown of how it works:

1. **Initialization:** The game starts by creating a grid of cells, with a hidden number of mines randomly placed within the grid.

2. **Player's Turn:** The player clicks on a cell.

   • **If the cell contains a mine:** The game is over, and the player loses.
   
   • **If the cell is safe:** The cell is revealed, and the number of adjacent mines is displayed.`,
    citations: [
      { file: "minesweeper/minesweeper.py", lines: "1-45" },
      { file: "minesweeper/assets/images/mine.png" },
    ],
  },
];

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>(demoMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    setMessages([...messages, newMessage]);
    setInput("");

    // Simulate AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I'll analyze that for you. Let me look through the codebase...",
          citations: [{ file: "minesweeper/minesweeper.py" }],
        },
      ]);
    }, 1000);
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
              placeholder="Ask about the codebase..."
              rows={1}
              className="w-full resize-none px-4 py-3 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-3 rounded-xl bg-arb-accent hover:bg-arb-accent/80 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-glow"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
