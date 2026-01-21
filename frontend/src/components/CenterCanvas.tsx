"use client";

import { MessageSquare, GitBranch, Clock, Volume2, FileCode2 } from "lucide-react";
import clsx from "clsx";
import { GraphViewer } from "./GraphViewer";
import { ChatPanel } from "./ChatPanel";
import { ChangeSetPanel } from "./ChangeSetPanel";

type TabType = "chat" | "graph" | "timeline" | "changes";

interface CenterCanvasProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
  { id: "chat", label: "Chat", icon: <MessageSquare className="w-4 h-4" /> },
  { id: "graph", label: "Graph", icon: <GitBranch className="w-4 h-4" /> },
  { id: "changes", label: "Changes", icon: <FileCode2 className="w-4 h-4" /> },
  { id: "timeline", label: "Timeline", icon: <Clock className="w-4 h-4" /> },
];

export function CenterCanvas({ activeTab, onTabChange }: CenterCanvasProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Tab Bar */}
      <div className="flex-shrink-0 border-b border-arb-border bg-arb-panel">
        <div className="flex items-center justify-between px-4">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={clsx(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors relative",
                  activeTab === tab.id
                    ? "text-arb-accent tab-active"
                    : "text-arb-text-dim hover:text-arb-text"
                )}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Audio toggle (from screenshot) */}
          <button className="p-2 rounded-lg hover:bg-arb-surface transition-colors">
            <Volume2 className="w-4 h-4 text-arb-text-dim" />
          </button>
        </div>
      </div>

      {/* Canvas Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === "graph" && <GraphViewer />}
        {activeTab === "chat" && <ChatPanel />}
        {activeTab === "changes" && <ChangeSetPanel />}
        {activeTab === "timeline" && (
          <div className="flex items-center justify-center h-full text-arb-text-muted">
            <div className="text-center">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Timeline view coming soon</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
