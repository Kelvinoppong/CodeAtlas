"use client";

import { useState, useEffect } from "react";
import { FolderOpen, Loader2, X, Sparkles, ChevronRight, ArrowUp, Folder, Check } from "lucide-react";
import api, { DirectoryEntry } from "@/lib/api";
import { useAppStore } from "@/lib/store";

interface ProjectImportProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function ProjectImport({ onClose, onSuccess }: ProjectImportProps) {
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");

  // Browser state
  const [showBrowser, setShowBrowser] = useState(false);
  const [browserPath, setBrowserPath] = useState("~");
  const [browserEntries, setBrowserEntries] = useState<DirectoryEntry[]>([]);
  const [browserParent, setBrowserParent] = useState<string | null>(null);
  const [isBrowsing, setIsBrowsing] = useState(false);

  const { setCurrentProject, setCurrentSnapshot, setFileTree } = useAppStore();

  // Load directory contents
  const loadDirectory = async (dirPath: string) => {
    setIsBrowsing(true);
    try {
      const result = await api.browseDirectory(dirPath);
      setBrowserPath(result.current_path);
      setBrowserEntries(result.entries);
      setBrowserParent(result.parent_path);
    } catch (err) {
      console.error("Failed to browse directory:", err);
    } finally {
      setIsBrowsing(false);
    }
  };

  // Open browser
  const handleOpenBrowser = () => {
    setShowBrowser(true);
    loadDirectory(path || "~");
  };

  // Select folder
  const handleSelectFolder = (folderPath: string) => {
    setPath(folderPath);
    // Auto-fill name from folder name if empty
    if (!name) {
      const folderName = folderPath.split("/").pop() || "";
      setName(folderName);
    }
    setShowBrowser(false);
  };

  // Navigate to parent
  const handleGoUp = () => {
    if (browserParent) {
      loadDirectory(browserParent);
    }
  };

  const handleImport = async () => {
    if (!name.trim() || !path.trim()) {
      setError("Please provide both project name and path");
      return;
    }

    setIsLoading(true);
    setError(null);
    setStatus("Creating project...");

    try {
      // Import project
      const importResult = await api.importProject(name, path);
      setStatus("Indexing files...");

      // Create snapshot (synchronous for now)
      const snapshotResult = await api.createSnapshotSync(importResult.id);
      setStatus("Loading file tree...");

      // Get project details
      const project = await api.getProject(importResult.id);
      setCurrentProject(project);

      // Get snapshot status
      const snapshot = await api.getSnapshotStatus(snapshotResult.snapshot_id);
      setCurrentSnapshot(snapshot);

      // Load file tree
      const tree = await api.getFileTree(snapshotResult.snapshot_id);
      setFileTree(tree);

      setStatus("Done!");
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-arb-panel border border-arb-border rounded-xl w-full max-w-lg p-6 shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center shadow-glow">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-display font-semibold">Import Project</h2>
              <p className="text-sm text-arb-text-dim">Add a local repository</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-arb-surface transition-colors"
          >
            <X className="w-5 h-5 text-arb-text-dim" />
          </button>
        </div>

        {!showBrowser ? (
          <>
            {/* Form */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-arb-text-dim mb-1.5">
                  Project Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Awesome Project"
                  className="w-full h-10 px-3 bg-arb-surface border border-arb-border rounded-lg text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-arb-text-dim mb-1.5">
                  Project Folder
                </label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
                    <input
                      type="text"
                      value={path}
                      onChange={(e) => setPath(e.target.value)}
                      placeholder="Click Browse to select..."
                      className="w-full h-10 pl-10 pr-3 bg-arb-surface border border-arb-border rounded-lg text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
                      disabled={isLoading}
                      readOnly
                    />
                  </div>
                  <button
                    onClick={handleOpenBrowser}
                    disabled={isLoading}
                    className="px-4 h-10 bg-arb-surface border border-arb-border rounded-lg hover:bg-arb-hover transition-colors text-sm font-medium"
                  >
                    Browse
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 bg-arb-error/10 border border-arb-error/30 rounded-lg text-sm text-arb-error">
                  {error}
                </div>
              )}

              {/* Status */}
              {isLoading && status && (
                <div className="flex items-center gap-2 text-sm text-arb-text-dim">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {status}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm rounded-lg hover:bg-arb-surface transition-colors"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={isLoading || !name.trim() || !path.trim()}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-arb-accent hover:bg-arb-accent/80 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-all shadow-glow"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FolderOpen className="w-4 h-4" />
                )}
                Import Project
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Folder Browser */}
            <div className="space-y-3">
              {/* Current path */}
              <div className="flex items-center gap-2 p-2 bg-arb-surface rounded-lg border border-arb-border">
                <button
                  onClick={handleGoUp}
                  disabled={!browserParent || isBrowsing}
                  className="p-1.5 rounded hover:bg-arb-hover disabled:opacity-30 transition-colors"
                  title="Go up"
                >
                  <ArrowUp className="w-4 h-4" />
                </button>
                <div className="flex-1 text-sm text-arb-text-dim truncate font-mono">
                  {browserPath}
                </div>
                {isBrowsing && <Loader2 className="w-4 h-4 animate-spin text-arb-accent" />}
              </div>

              {/* Directory listing */}
              <div className="h-64 overflow-y-auto border border-arb-border rounded-lg bg-arb-surface">
                {browserEntries.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-sm text-arb-text-muted">
                    {isBrowsing ? "Loading..." : "Empty directory"}
                  </div>
                ) : (
                  <div className="divide-y divide-arb-border/50">
                    {browserEntries.map((entry) => (
                      <div
                        key={entry.path}
                        className="flex items-center gap-2 px-3 py-2 hover:bg-arb-hover cursor-pointer transition-colors"
                        onClick={() => {
                          if (entry.is_dir) {
                            loadDirectory(entry.path);
                          }
                        }}
                      >
                        <Folder className={`w-4 h-4 ${entry.is_dir ? "text-arb-accent" : "text-arb-text-muted"}`} />
                        <span className="flex-1 text-sm truncate">{entry.name}</span>
                        {entry.is_dir && (
                          <ChevronRight className="w-4 h-4 text-arb-text-muted" />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Browser actions */}
              <div className="flex justify-between items-center">
                <p className="text-xs text-arb-text-muted">
                  Navigate to your project folder, then click Select
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowBrowser(false)}
                    className="px-3 py-1.5 text-sm rounded-lg hover:bg-arb-surface transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleSelectFolder(browserPath)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-arb-accent hover:bg-arb-accent/80 rounded-lg transition-all"
                  >
                    <Check className="w-4 h-4" />
                    Select This Folder
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
