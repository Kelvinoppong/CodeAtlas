"use client";

import { useState, useEffect } from "react";
import {
  GitCommit,
  GitBranch,
  Clock,
  User,
  FileCode,
  ChevronRight,
  Loader2,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/lib/store";
import api, { GitCommit as GitCommitType, GitBranch as GitBranchType, GitStatus } from "@/lib/api";

interface CommitNodeProps {
  commit: GitCommitType;
  isFirst: boolean;
  isLast: boolean;
  onSelect: () => void;
  isSelected: boolean;
}

function CommitNode({ commit, isFirst, isLast, onSelect, isSelected }: CommitNodeProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return `${diffMins}m ago`;
      }
      return `${diffHours}h ago`;
    } else if (diffDays === 1) {
      return "Yesterday";
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
  };

  return (
    <div className="flex gap-4">
      {/* Timeline line */}
      <div className="flex flex-col items-center w-8">
        {!isFirst && <div className="w-0.5 h-4 bg-arb-border" />}
        <div
          className={clsx(
            "w-4 h-4 rounded-full border-2 flex-shrink-0 transition-all",
            isSelected
              ? "bg-arb-accent border-arb-accent shadow-glow"
              : "bg-arb-surface border-arb-border hover:border-arb-accent/50"
          )}
        />
        {!isLast && <div className="w-0.5 flex-1 bg-arb-border min-h-[40px]" />}
      </div>

      {/* Commit card */}
      <button
        onClick={onSelect}
        className={clsx(
          "flex-1 text-left p-4 rounded-xl border transition-all mb-2",
          isSelected
            ? "bg-arb-accent/10 border-arb-accent"
            : "bg-arb-surface border-arb-border hover:border-arb-accent/50"
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <p className="font-medium text-arb-text truncate">{commit.message}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-arb-text-dim">
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {commit.author}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDate(commit.date)}
              </span>
            </div>
          </div>
          <code className="flex-shrink-0 px-2 py-1 bg-arb-bg rounded text-xs font-mono text-arb-accent">
            {commit.short_sha}
          </code>
        </div>
      </button>
    </div>
  );
}

interface BranchSelectorProps {
  branches: GitBranchType[];
  currentBranch: string | null;
  selectedBranch: string | null;
  onSelect: (branch: string) => void;
}

function BranchSelector({ branches, currentBranch, selectedBranch, onSelect }: BranchSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-arb-surface border border-arb-border rounded-lg text-sm hover:border-arb-accent/50 transition-colors"
      >
        <GitBranch className="w-4 h-4 text-arb-accent" />
        <span className="font-medium">{selectedBranch || currentBranch || "Select branch"}</span>
        <ChevronRight
          className={clsx(
            "w-4 h-4 text-arb-text-dim transition-transform",
            isOpen && "rotate-90"
          )}
        />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 mt-2 w-64 bg-arb-panel border border-arb-border rounded-xl shadow-xl z-50 overflow-hidden">
            <div className="p-2 max-h-64 overflow-y-auto">
              {branches.map((branch) => (
                <button
                  key={branch.name}
                  onClick={() => {
                    onSelect(branch.name);
                    setIsOpen(false);
                  }}
                  className={clsx(
                    "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                    branch.name === selectedBranch
                      ? "bg-arb-accent/20 text-arb-accent"
                      : "hover:bg-arb-hover text-arb-text"
                  )}
                >
                  <GitBranch className="w-4 h-4" />
                  <span className="truncate flex-1 text-left">{branch.name}</span>
                  {branch.is_current && (
                    <span className="px-1.5 py-0.5 bg-arb-accent/20 text-arb-accent text-xs rounded">
                      HEAD
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function TimelinePanel() {
  const { currentSnapshot } = useAppStore();
  const [commits, setCommits] = useState<GitCommitType[]>([]);
  const [branches, setBranches] = useState<GitBranchType[]>([]);
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
  const [selectedCommit, setSelectedCommit] = useState<GitCommitType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load git data
  useEffect(() => {
    if (!currentSnapshot) return;
    loadGitData();
  }, [currentSnapshot]);

  // Load commits when branch changes
  useEffect(() => {
    if (!currentSnapshot) return;
    loadCommits();
  }, [currentSnapshot, selectedBranch]);

  const loadGitData = async () => {
    if (!currentSnapshot) return;
    setIsLoading(true);
    setError(null);

    try {
      const [statusResult, branchesResult] = await Promise.all([
        api.getGitStatus(currentSnapshot.id),
        api.getGitBranches(currentSnapshot.id),
      ]);

      setGitStatus(statusResult);
      setBranches(branchesResult);

      // Set selected branch to current branch
      if (statusResult.branch && !selectedBranch) {
        setSelectedBranch(statusResult.branch);
      }
    } catch (err) {
      console.error("Failed to load git data:", err);
      setError("Failed to load git information. Is this a git repository?");
    } finally {
      setIsLoading(false);
    }
  };

  const loadCommits = async () => {
    if (!currentSnapshot) return;
    setIsLoading(true);

    try {
      const commitsResult = await api.getGitCommits(
        currentSnapshot.id,
        50,
        selectedBranch || undefined
      );
      setCommits(commitsResult);
    } catch (err) {
      console.error("Failed to load commits:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentSnapshot) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-arb-text-muted p-8">
        <Clock className="w-12 h-12 mb-4 opacity-30" />
        <p className="text-center">Import a project to view commit history</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-arb-text-muted p-8">
        <AlertCircle className="w-12 h-12 mb-4 text-amber-500 opacity-60" />
        <p className="text-center mb-4">{error}</p>
        <button
          onClick={loadGitData}
          className="flex items-center gap-2 px-4 py-2 bg-arb-surface border border-arb-border rounded-lg hover:border-arb-accent/50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Left: Commit timeline */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-arb-border bg-arb-panel">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="font-semibold text-arb-text flex items-center gap-2">
                <GitCommit className="w-4 h-4 text-arb-accent" />
                Commit History
              </h2>
              {branches.length > 0 && (
                <BranchSelector
                  branches={branches}
                  currentBranch={gitStatus?.branch || null}
                  selectedBranch={selectedBranch}
                  onSelect={setSelectedBranch}
                />
              )}
            </div>

            <button
              onClick={loadGitData}
              disabled={isLoading}
              className="p-2 rounded-lg hover:bg-arb-surface transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={clsx(
                  "w-4 h-4 text-arb-text-dim",
                  isLoading && "animate-spin"
                )}
              />
            </button>
          </div>

          {/* Git status summary */}
          {gitStatus && gitStatus.has_changes && (
            <div className="mt-3 flex items-center gap-4 text-xs">
              {gitStatus.staged_files.length > 0 && (
                <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded">
                  {gitStatus.staged_files.length} staged
                </span>
              )}
              {gitStatus.modified_files.length > 0 && (
                <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded">
                  {gitStatus.modified_files.length} modified
                </span>
              )}
              {gitStatus.untracked_files.length > 0 && (
                <span className="px-2 py-1 bg-arb-surface text-arb-text-dim rounded">
                  {gitStatus.untracked_files.length} untracked
                </span>
              )}
            </div>
          )}
        </div>

        {/* Commits list */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading && commits.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 text-arb-accent animate-spin" />
            </div>
          ) : commits.length === 0 ? (
            <div className="text-center p-8 text-arb-text-muted">
              <GitCommit className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No commits found</p>
            </div>
          ) : (
            <div className="space-y-0">
              {commits.map((commit, index) => (
                <CommitNode
                  key={commit.sha}
                  commit={commit}
                  isFirst={index === 0}
                  isLast={index === commits.length - 1}
                  isSelected={selectedCommit?.sha === commit.sha}
                  onSelect={() => setSelectedCommit(commit)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Selected commit details */}
      <div className="w-80 flex-shrink-0 border-l border-arb-border overflow-hidden flex flex-col">
        {selectedCommit ? (
          <>
            <div className="p-4 border-b border-arb-border bg-arb-panel">
              <h3 className="font-semibold text-arb-text">Commit Details</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Commit info */}
              <div>
                <label className="text-xs text-arb-text-muted uppercase tracking-wide">
                  Message
                </label>
                <p className="mt-1 text-sm text-arb-text">{selectedCommit.message}</p>
              </div>

              <div>
                <label className="text-xs text-arb-text-muted uppercase tracking-wide">
                  SHA
                </label>
                <code className="block mt-1 px-3 py-2 bg-arb-bg rounded-lg text-xs font-mono text-arb-accent break-all">
                  {selectedCommit.sha}
                </code>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-arb-text-muted uppercase tracking-wide">
                    Author
                  </label>
                  <p className="mt-1 text-sm text-arb-text">{selectedCommit.author}</p>
                </div>
                <div>
                  <label className="text-xs text-arb-text-muted uppercase tracking-wide">
                    Date
                  </label>
                  <p className="mt-1 text-sm text-arb-text">
                    {new Date(selectedCommit.date).toLocaleString()}
                  </p>
                </div>
              </div>

              <div>
                <label className="text-xs text-arb-text-muted uppercase tracking-wide">
                  Email
                </label>
                <p className="mt-1 text-sm text-arb-text-dim">{selectedCommit.author_email}</p>
              </div>

              {/* Actions */}
              <div className="pt-4 border-t border-arb-border space-y-2">
                <button
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-arb-surface border border-arb-border rounded-lg text-sm hover:border-arb-accent/50 transition-colors"
                  onClick={() => {
                    navigator.clipboard.writeText(selectedCommit.sha);
                  }}
                >
                  <FileCode className="w-4 h-4" />
                  Copy SHA
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-arb-text-muted p-8">
            <GitCommit className="w-8 h-8 mb-3 opacity-30" />
            <p className="text-sm text-center">Select a commit to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
