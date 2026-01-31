"use client";

import { useState } from "react";
import { X, Settings, Cpu, Palette, Info, Check } from "lucide-react";
import clsx from "clsx";

interface SettingsModalProps {
  onClose: () => void;
}

type TabType = "ai" | "appearance" | "about";

export function SettingsModal({ onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("ai");
  const [aiProvider, setAiProvider] = useState(
    typeof window !== "undefined" 
      ? localStorage.getItem("ai_provider") || "ollama" 
      : "ollama"
  );
  const [ollamaModel, setOllamaModel] = useState(
    typeof window !== "undefined"
      ? localStorage.getItem("ollama_model") || "qwen2.5-coder:1.5b"
      : "qwen2.5-coder:1.5b"
  );
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem("ai_provider", aiProvider);
    localStorage.setItem("ollama_model", ollamaModel);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const tabs: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: "ai", label: "AI Settings", icon: <Cpu className="w-4 h-4" /> },
    { id: "appearance", label: "Appearance", icon: <Palette className="w-4 h-4" /> },
    { id: "about", label: "About", icon: <Info className="w-4 h-4" /> },
  ];

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-arb-panel border border-arb-border rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-arb-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-arb-text">Settings</h2>
              <p className="text-xs text-arb-text-dim">Configure CodeAtlas</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-arb-surface transition-colors"
          >
            <X className="w-5 h-5 text-arb-text-dim" />
          </button>
        </div>

        <div className="flex h-[400px]">
          {/* Sidebar */}
          <div className="w-48 border-r border-arb-border p-3 space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                  activeTab === tab.id
                    ? "bg-arb-accent/20 text-arb-accent"
                    : "text-arb-text-dim hover:text-arb-text hover:bg-arb-surface"
                )}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {activeTab === "ai" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-arb-text mb-3">AI Provider</h3>
                  <div className="space-y-2">
                    {[
                      { id: "ollama", label: "Ollama (Local)", desc: "Run AI locally, no API key needed" },
                      { id: "gemini", label: "Google Gemini", desc: "Cloud AI, requires API key" },
                      { id: "openai", label: "OpenAI", desc: "GPT models, requires API key" },
                    ].map((provider) => (
                      <label
                        key={provider.id}
                        className={clsx(
                          "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors",
                          aiProvider === provider.id
                            ? "border-arb-accent bg-arb-accent/10"
                            : "border-arb-border hover:border-arb-accent/50"
                        )}
                      >
                        <input
                          type="radio"
                          name="aiProvider"
                          value={provider.id}
                          checked={aiProvider === provider.id}
                          onChange={(e) => setAiProvider(e.target.value)}
                          className="mt-1 accent-arb-accent"
                        />
                        <div>
                          <div className="font-medium text-arb-text text-sm">{provider.label}</div>
                          <div className="text-xs text-arb-text-dim">{provider.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {aiProvider === "ollama" && (
                  <div>
                    <h3 className="text-sm font-medium text-arb-text mb-3">Ollama Model</h3>
                    <select
                      value={ollamaModel}
                      onChange={(e) => setOllamaModel(e.target.value)}
                      className="w-full px-4 py-2 bg-arb-surface border border-arb-border rounded-lg text-sm focus:outline-none focus:border-arb-accent/50"
                    >
                      <option value="qwen2.5-coder:1.5b">qwen2.5-coder:1.5b (Fast, CPU friendly)</option>
                      <option value="qwen2.5-coder:3b">qwen2.5-coder:3b (Balanced)</option>
                      <option value="qwen2.5-coder:7b">qwen2.5-coder:7b (Best quality, needs GPU)</option>
                      <option value="codellama:7b">codellama:7b</option>
                      <option value="deepseek-coder:6.7b">deepseek-coder:6.7b</option>
                    </select>
                    <p className="text-xs text-arb-text-muted mt-2">
                      Note: Changing settings here only affects the frontend display. 
                      To change the actual AI model, update the backend .env file.
                    </p>
                  </div>
                )}

                <button
                  onClick={handleSave}
                  className="flex items-center gap-2 px-4 py-2 bg-arb-accent text-white rounded-lg text-sm font-medium hover:bg-arb-accent/80 transition-colors"
                >
                  {saved ? <Check className="w-4 h-4" /> : null}
                  {saved ? "Saved!" : "Save Settings"}
                </button>
              </div>
            )}

            {activeTab === "appearance" && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-arb-text mb-3">Theme</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-4 rounded-lg border-2 border-arb-accent bg-arb-bg cursor-pointer">
                      <div className="w-full h-16 rounded bg-gradient-to-br from-[#0a0a0f] to-[#1a1a2e] mb-2" />
                      <div className="text-sm font-medium text-arb-text">Dark (Default)</div>
                    </div>
                    <div className="p-4 rounded-lg border border-arb-border bg-arb-surface cursor-not-allowed opacity-50">
                      <div className="w-full h-16 rounded bg-gradient-to-br from-gray-100 to-gray-200 mb-2" />
                      <div className="text-sm font-medium text-arb-text-dim">Light (Coming soon)</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-arb-text mb-3">Accent Color</h3>
                  <div className="flex gap-2">
                    {["#a78bfa", "#f472b6", "#34d399", "#60a5fa", "#fbbf24"].map((color) => (
                      <button
                        key={color}
                        className={clsx(
                          "w-8 h-8 rounded-full border-2 transition-transform hover:scale-110",
                          color === "#a78bfa" ? "border-white" : "border-transparent"
                        )}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-arb-text-muted mt-2">
                    Color customization coming soon
                  </p>
                </div>
              </div>
            )}

            {activeTab === "about" && (
              <div className="space-y-6">
                <div className="text-center py-4">
                  <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center mb-4 shadow-glow">
                    <span className="text-2xl">🗺️</span>
                  </div>
                  <h3 className="text-xl font-semibold text-arb-text">CodeAtlas</h3>
                  <p className="text-sm text-arb-text-dim mt-1">Version 0.1.0</p>
                </div>

                <div className="bg-arb-surface rounded-lg p-4 space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-arb-text-dim">Frontend</span>
                    <span className="text-arb-text">Next.js 14 + React 18</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-arb-text-dim">Backend</span>
                    <span className="text-arb-text">FastAPI + Python 3.11</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-arb-text-dim">AI Engine</span>
                    <span className="text-arb-text">Ollama (Local LLM)</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-arb-text-dim">Database</span>
                    <span className="text-arb-text">PostgreSQL + pgvector</span>
                  </div>
                </div>

                <p className="text-xs text-arb-text-muted text-center">
                  Navigate your codebase like never before.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
