"use client";

import { useState } from "react";
import { FolderOpen, Loader2, X, Sparkles } from "lucide-react";
import api from "@/lib/api";
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

  const { setCurrentProject, setCurrentSnapshot, setFileTree } = useAppStore();

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
      <div className="bg-arb-panel border border-arb-border rounded-xl w-full max-w-md p-6 shadow-2xl animate-slide-up">
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
              Local Path
            </label>
            <div className="relative">
              <FolderOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
              <input
                type="text"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder="/path/to/your/project"
                className="w-full h-10 pl-10 pr-3 bg-arb-surface border border-arb-border rounded-lg text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-1 focus:ring-arb-accent/20 transition-all"
                disabled={isLoading}
              />
            </div>
            <p className="mt-1 text-xs text-arb-text-muted">
              Enter the absolute path to your project directory
            </p>
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
      </div>
    </div>
  );
}
