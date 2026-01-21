"use client";

import { useState } from "react";
import { Search, Download, Settings, Sparkles, FolderOpen } from "lucide-react";
import { useAppStore } from "@/lib/store";
import { useAuthStore } from "@/lib/authStore";
import api from "@/lib/api";
import { UserMenu } from "./UserMenu";
import { PresenceIndicator } from "./PresenceIndicator";

interface HeaderProps {
  onImportClick: () => void;
  onLoginClick: () => void;
}

export function Header({ onImportClick, onLoginClick }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const { currentProject, currentSnapshot, setSelectedFile } = useAppStore();
  const { isAuthenticated } = useAuthStore();

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    
    if (!query.trim() || !currentSnapshot) {
      setSearchResults([]);
      return;
    }

    try {
      const symbols = await api.searchSymbols(currentSnapshot.id, query);
      setSearchResults(symbols.slice(0, 10));
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  const handleResultClick = (result: any) => {
    setSelectedFile(result.file_path);
    setSearchQuery("");
    setSearchResults([]);
    setShowSearch(false);
  };

  return (
    <header className="h-14 flex-shrink-0 border-b border-arb-border bg-arb-panel flex items-center justify-between px-4">
      {/* Logo & Brand */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center shadow-glow">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div>
          <span className="font-display text-lg font-semibold tracking-tight">
            CodeAtlas
          </span>
          {currentProject && (
            <span className="ml-2 text-sm text-arb-text-dim">
              / {currentProject.name}
            </span>
          )}
        </div>
      </div>

      {/* Center - Search */}
      <div className="flex-1 max-w-xl mx-8 relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
          <input
            type="text"
            placeholder="Search files, symbols, or ask a question..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => setShowSearch(true)}
            className="w-full h-9 pl-10 pr-4 bg-arb-surface border border-arb-border rounded-lg text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-arb-text-muted bg-arb-bg px-1.5 py-0.5 rounded border border-arb-border">
            ⌘K
          </kbd>
        </div>

        {/* Search Results Dropdown */}
        {showSearch && searchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-arb-panel border border-arb-border rounded-lg shadow-xl z-50 overflow-hidden">
            <div className="p-2">
              {searchResults.map((result) => (
                <button
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-md hover:bg-arb-hover text-left transition-colors"
                >
                  <span className="text-xs px-1.5 py-0.5 rounded bg-arb-surface text-arb-text-dim">
                    {result.kind}
                  </span>
                  <span className="font-medium">{result.name}</span>
                  <span className="text-xs text-arb-text-muted truncate flex-1">
                    {result.file_path}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Close search on outside click */}
        {showSearch && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowSearch(false)}
          />
        )}
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Presence indicator */}
        {currentProject && isAuthenticated && (
          <PresenceIndicator projectId={currentProject.id} />
        )}
        
        <div className="flex items-center gap-2">
          <button
            onClick={onImportClick}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-arb-surface border border-arb-border rounded-lg hover:bg-arb-hover hover:border-arb-accent/30 transition-all"
          >
            <FolderOpen className="w-4 h-4" />
            <span className="hidden sm:inline">Import</span>
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-arb-surface border border-arb-border rounded-lg hover:bg-arb-hover hover:border-arb-accent/30 transition-all">
            <Download className="w-4 h-4" />
            <span className="hidden sm:inline">Export</span>
          </button>
          <button className="p-2 rounded-lg hover:bg-arb-surface transition-colors">
            <Settings className="w-5 h-5 text-arb-text-dim" />
          </button>
        </div>
        
        {/* User menu / login */}
        <div className="border-l border-arb-border pl-3 ml-1">
          <UserMenu onLoginClick={onLoginClick} />
        </div>
      </div>
    </header>
  );
}
