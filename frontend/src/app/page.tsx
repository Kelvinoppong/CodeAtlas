"use client";

import { useState } from "react";
import { FileTree } from "@/components/FileTree";
import { CenterCanvas } from "@/components/CenterCanvas";
import { CodeEditor } from "@/components/CodeEditor";
import { Header } from "@/components/Header";

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "graph" | "timeline">("graph");

  return (
    <div className="h-screen w-screen flex flex-col bg-arb-bg overflow-hidden">
      {/* Top Header */}
      <Header />

      {/* Main 3-Pane Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - File Tree */}
        <aside className="w-72 flex-shrink-0 border-r border-arb-border bg-arb-panel flex flex-col animate-fade-in">
          <FileTree onFileSelect={setSelectedFile} selectedFile={selectedFile} />
        </aside>

        {/* Center Panel - Graph/Chat Canvas */}
        <main className="flex-1 flex flex-col overflow-hidden bg-arb-bg animate-fade-in">
          <CenterCanvas activeTab={activeTab} onTabChange={setActiveTab} />
        </main>

        {/* Right Panel - Code Editor */}
        <aside className="w-[480px] flex-shrink-0 border-l border-arb-border bg-arb-panel flex flex-col animate-fade-in">
          <CodeEditor selectedFile={selectedFile} />
        </aside>
      </div>
    </div>
  );
}
