"use client";

import { Search, Download, Settings, Sparkles } from "lucide-react";

export function Header() {
  return (
    <header className="h-14 flex-shrink-0 border-b border-arb-border bg-arb-panel flex items-center justify-between px-4">
      {/* Logo & Brand */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center shadow-glow">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="font-display text-lg font-semibold tracking-tight">
          CodeAtlas
        </span>
      </div>

      {/* Center - Search */}
      <div className="flex-1 max-w-xl mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
          <input
            type="text"
            placeholder="Search files, symbols, or ask a question..."
            className="w-full h-9 pl-10 pr-4 bg-arb-surface border border-arb-border rounded-lg text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-arb-text-muted bg-arb-bg px-1.5 py-0.5 rounded border border-arb-border">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-arb-surface border border-arb-border rounded-lg hover:bg-arb-hover hover:border-arb-accent/30 transition-all">
          <Download className="w-4 h-4" />
          <span>Export</span>
        </button>
        <button className="p-2 rounded-lg hover:bg-arb-surface transition-colors">
          <Settings className="w-5 h-5 text-arb-text-dim" />
        </button>
      </div>
    </header>
  );
}
