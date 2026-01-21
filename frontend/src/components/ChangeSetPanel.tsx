"use client";

import { useState, useEffect } from "react";
import {
  GitBranch,
  Play,
  RotateCcw,
  GitCommit,
  Trash2,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  FileCode,
  Loader2,
  ShieldAlert,
  Info,
} from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/lib/store";
import api, { ChangeSet, Patch } from "@/lib/api";
import { DiffViewer } from "./DiffViewer";

type StatusType = ChangeSet["status"];

const statusConfig: Record<StatusType, { icon: React.ReactNode; color: string; label: string }> = {
  proposed: {
    icon: <Clock className="w-4 h-4" />,
    color: "text-amber-400",
    label: "Proposed",
  },
  applied: {
    icon: <CheckCircle2 className="w-4 h-4" />,
    color: "text-emerald-400",
    label: "Applied",
  },
  rolled_back: {
    icon: <RotateCcw className="w-4 h-4" />,
    color: "text-arb-text-muted",
    label: "Rolled Back",
  },
  rejected: {
    icon: <XCircle className="w-4 h-4" />,
    color: "text-rose-400",
    label: "Rejected",
  },
};

const riskColors: Record<string, string> = {
  low: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  critical: "bg-rose-500/20 text-rose-400 border-rose-500/30",
};

interface ChangeSetCardProps {
  changeSet: ChangeSet;
  isSelected: boolean;
  onSelect: () => void;
  onApply: () => void;
  onRollback: () => void;
  onCommit: () => void;
  onDelete: () => void;
  isLoading: boolean;
}

function ChangeSetCard({
  changeSet,
  isSelected,
  onSelect,
  onApply,
  onRollback,
  onCommit,
  onDelete,
  isLoading,
}: ChangeSetCardProps) {
  const status = statusConfig[changeSet.status];
  const canApply = changeSet.status === "proposed";
  const canRollback = changeSet.status === "applied";
  const canCommit = changeSet.status === "applied" && !changeSet.git_commit_sha;
  const canDelete = changeSet.status !== "applied";
  
  return (
    <div
      className={clsx(
        "border rounded-xl p-4 transition-all cursor-pointer",
        isSelected
          ? "border-arb-accent bg-arb-accent/5"
          : "border-arb-border bg-arb-surface hover:border-arb-accent/50"
      )}
      onClick={onSelect}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-arb-text truncate">{changeSet.title}</h3>
          <p className="text-xs text-arb-text-muted mt-1">
            {changeSet.patches.length} file{changeSet.patches.length !== 1 ? "s" : ""} •{" "}
            {new Date(changeSet.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className={clsx("flex items-center gap-1.5 text-xs font-medium", status.color)}>
          {status.icon}
          {status.label}
        </div>
      </div>
      
      {/* Rationale */}
      {changeSet.rationale && (
        <p className="text-sm text-arb-text-dim mt-2 line-clamp-2">{changeSet.rationale}</p>
      )}
      
      {/* Git commit info */}
      {changeSet.git_commit_sha && (
        <div className="flex items-center gap-2 mt-3 text-xs text-arb-text-muted">
          <GitCommit className="w-3 h-3" />
          <span className="font-mono">{changeSet.git_commit_sha.slice(0, 7)}</span>
          <span className="truncate">{changeSet.git_commit_message}</span>
        </div>
      )}
      
      {/* Actions */}
      <div className="flex items-center gap-2 mt-4" onClick={(e) => e.stopPropagation()}>
        {canApply && (
          <button
            onClick={onApply}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-medium hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
            Apply
          </button>
        )}
        {canRollback && (
          <button
            onClick={onRollback}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-medium hover:bg-amber-500/30 transition-colors disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
            Rollback
          </button>
        )}
        {canCommit && (
          <button
            onClick={onCommit}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-arb-accent/20 text-arb-accent text-xs font-medium hover:bg-arb-accent/30 transition-colors disabled:opacity-50"
          >
            <GitCommit className="w-3 h-3" />
            Commit
          </button>
        )}
        {canDelete && (
          <button
            onClick={onDelete}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 text-rose-400 text-xs font-medium hover:bg-rose-500/20 transition-colors disabled:opacity-50 ml-auto"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}

interface PatchViewerProps {
  patches: Patch[];
}

function PatchViewer({ patches }: PatchViewerProps) {
  const [expandedPatches, setExpandedPatches] = useState<Set<string>>(new Set(patches.map(p => p.id)));
  
  const togglePatch = (id: string) => {
    const newExpanded = new Set(expandedPatches);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedPatches(newExpanded);
  };
  
  return (
    <div className="space-y-4">
      {patches.map((patch) => (
        <div key={patch.id} className="border border-arb-border rounded-xl overflow-hidden">
          {/* Patch header */}
          <button
            onClick={() => togglePatch(patch.id)}
            className="w-full flex items-center gap-2 px-4 py-3 bg-arb-surface hover:bg-arb-hover transition-colors"
          >
            {expandedPatches.has(patch.id) ? (
              <ChevronDown className="w-4 h-4 text-arb-text-dim" />
            ) : (
              <ChevronRight className="w-4 h-4 text-arb-text-dim" />
            )}
            <FileCode className="w-4 h-4 text-arb-accent" />
            <span className="font-mono text-sm text-arb-text">{patch.file_path}</span>
          </button>
          
          {/* Patch diff */}
          {expandedPatches.has(patch.id) && (
            <DiffViewer diff={patch.diff} filePath={patch.file_path} showHeader={false} />
          )}
        </div>
      ))}
    </div>
  );
}

export function ChangeSetPanel() {
  const {
    currentSnapshot,
    changeSets,
    setChangeSets,
    selectedChangeSet,
    setSelectedChangeSet,
    isLoadingChangeSets,
    setIsLoadingChangeSets,
    currentImpact,
    setCurrentImpact,
  } = useAppStore();
  
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [commitMessage, setCommitMessage] = useState("");
  const [showCommitDialog, setShowCommitDialog] = useState(false);
  const [pendingCommitId, setPendingCommitId] = useState<string | null>(null);
  
  // Load changesets
  useEffect(() => {
    if (currentSnapshot) {
      loadChangeSets();
    }
  }, [currentSnapshot]);
  
  const loadChangeSets = async () => {
    if (!currentSnapshot) return;
    setIsLoadingChangeSets(true);
    try {
      const result = await api.listChangeSets(currentSnapshot.id);
      setChangeSets(result);
    } catch (err) {
      console.error("Failed to load changesets:", err);
    } finally {
      setIsLoadingChangeSets(false);
    }
  };
  
  const handleApply = async (id: string) => {
    setActionLoading(id);
    try {
      await api.applyChangeSet(id);
      await loadChangeSets();
      // Reload the selected changeset
      if (selectedChangeSet?.id === id) {
        const updated = await api.getChangeSet(id);
        setSelectedChangeSet(updated);
      }
    } catch (err) {
      console.error("Failed to apply changeset:", err);
    } finally {
      setActionLoading(null);
    }
  };
  
  const handleRollback = async (id: string) => {
    setActionLoading(id);
    try {
      await api.rollbackChangeSet(id);
      await loadChangeSets();
      if (selectedChangeSet?.id === id) {
        const updated = await api.getChangeSet(id);
        setSelectedChangeSet(updated);
      }
    } catch (err) {
      console.error("Failed to rollback changeset:", err);
    } finally {
      setActionLoading(null);
    }
  };
  
  const handleCommit = async () => {
    if (!pendingCommitId || !commitMessage.trim()) return;
    setActionLoading(pendingCommitId);
    try {
      await api.commitChangeSet(pendingCommitId, commitMessage);
      await loadChangeSets();
      if (selectedChangeSet?.id === pendingCommitId) {
        const updated = await api.getChangeSet(pendingCommitId);
        setSelectedChangeSet(updated);
      }
      setShowCommitDialog(false);
      setCommitMessage("");
      setPendingCommitId(null);
    } catch (err) {
      console.error("Failed to commit changeset:", err);
    } finally {
      setActionLoading(null);
    }
  };
  
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this changeset?")) return;
    setActionLoading(id);
    try {
      await api.deleteChangeSet(id);
      await loadChangeSets();
      if (selectedChangeSet?.id === id) {
        setSelectedChangeSet(null);
      }
    } catch (err) {
      console.error("Failed to delete changeset:", err);
    } finally {
      setActionLoading(null);
    }
  };
  
  const analyzeImpact = async (changeSet: ChangeSet) => {
    if (!currentSnapshot) return;
    try {
      const files = changeSet.patches.map((p) => p.file_path);
      const impact = await api.analyzeImpact(currentSnapshot.id, files);
      setCurrentImpact(impact);
    } catch (err) {
      console.error("Failed to analyze impact:", err);
    }
  };
  
  if (!currentSnapshot) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-arb-text-muted p-8">
        <GitBranch className="w-12 h-12 mb-4 opacity-30" />
        <p className="text-center">Import a project to manage changes</p>
      </div>
    );
  }
  
  return (
    <div className="flex h-full">
      {/* Left: ChangeSet list */}
      <div className="w-80 flex-shrink-0 border-r border-arb-border overflow-hidden flex flex-col">
        <div className="p-4 border-b border-arb-border">
          <h2 className="font-semibold text-arb-text flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-arb-accent" />
            ChangeSets
          </h2>
          <p className="text-xs text-arb-text-muted mt-1">
            {changeSets.length} changeset{changeSets.length !== 1 ? "s" : ""}
          </p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {isLoadingChangeSets ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 text-arb-accent animate-spin" />
            </div>
          ) : changeSets.length === 0 ? (
            <div className="text-center p-8 text-arb-text-muted">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No changesets yet</p>
              <p className="text-xs mt-1">Use AI to propose code changes</p>
            </div>
          ) : (
            changeSets.map((cs) => (
              <ChangeSetCard
                key={cs.id}
                changeSet={cs}
                isSelected={selectedChangeSet?.id === cs.id}
                onSelect={() => {
                  setSelectedChangeSet(cs);
                  analyzeImpact(cs);
                }}
                onApply={() => handleApply(cs.id)}
                onRollback={() => handleRollback(cs.id)}
                onCommit={() => {
                  setPendingCommitId(cs.id);
                  setCommitMessage(cs.title);
                  setShowCommitDialog(true);
                }}
                onDelete={() => handleDelete(cs.id)}
                isLoading={actionLoading === cs.id}
              />
            ))
          )}
        </div>
      </div>
      
      {/* Right: Selected changeset details */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {selectedChangeSet ? (
          <>
            {/* Header */}
            <div className="p-4 border-b border-arb-border bg-arb-panel">
              <h2 className="font-semibold text-arb-text">{selectedChangeSet.title}</h2>
              {selectedChangeSet.rationale && (
                <p className="text-sm text-arb-text-dim mt-1">{selectedChangeSet.rationale}</p>
              )}
            </div>
            
            {/* Impact analysis banner */}
            {currentImpact && (
              <div
                className={clsx(
                  "mx-4 mt-4 p-3 rounded-lg border flex items-start gap-3",
                  riskColors[currentImpact.risk_level]
                )}
              >
                <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium text-sm">
                    {currentImpact.risk_level.charAt(0).toUpperCase() + currentImpact.risk_level.slice(1)} Risk
                  </div>
                  <p className="text-xs mt-0.5 opacity-80">{currentImpact.risk_explanation}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs">
                    <span>{currentImpact.total_files_affected} files affected</span>
                    <span>{currentImpact.total_symbols_affected} symbols affected</span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Patches */}
            <div className="flex-1 overflow-y-auto p-4">
              <PatchViewer patches={selectedChangeSet.patches} />
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-arb-text-muted">
            <FileCode className="w-12 h-12 mb-4 opacity-30" />
            <p>Select a changeset to view details</p>
          </div>
        )}
      </div>
      
      {/* Commit dialog */}
      {showCommitDialog && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-arb-panel border border-arb-border rounded-2xl p-6 w-full max-w-md animate-scale-in">
            <h3 className="text-lg font-semibold text-arb-text mb-4 flex items-center gap-2">
              <GitCommit className="w-5 h-5 text-arb-accent" />
              Create Git Commit
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-arb-text-dim block mb-2">Commit Message</label>
                <textarea
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Enter commit message..."
                  rows={3}
                  className="w-full px-4 py-3 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 resize-none"
                />
              </div>
              
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowCommitDialog(false);
                    setCommitMessage("");
                    setPendingCommitId(null);
                  }}
                  className="px-4 py-2 rounded-lg text-arb-text-dim hover:text-arb-text transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCommit}
                  disabled={!commitMessage.trim() || actionLoading !== null}
                  className="px-4 py-2 rounded-lg bg-arb-accent text-white font-medium hover:bg-arb-accent/80 transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {actionLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <GitCommit className="w-4 h-4" />
                  )}
                  Commit
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
