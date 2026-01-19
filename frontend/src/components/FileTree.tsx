"use client";

import { useState, useEffect } from "react";
import {
  ChevronRight,
  ChevronDown,
  File,
  Folder,
  FolderOpen,
  Search,
  FileCode,
  FileJson,
  FileText,
  Image,
  Plus,
  RefreshCw,
} from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/lib/store";
import api, { FileTreeNode } from "@/lib/api";

function getFileIcon(node: FileTreeNode) {
  if (node.type === "folder") return null;

  const ext = node.name.split(".").pop()?.toLowerCase();

  switch (ext) {
    case "py":
      return <FileCode className="w-4 h-4 text-yellow-400" />;
    case "js":
    case "ts":
    case "tsx":
    case "jsx":
      return <FileCode className="w-4 h-4 text-blue-400" />;
    case "json":
      return <FileJson className="w-4 h-4 text-amber-400" />;
    case "md":
    case "mdx":
      return <FileText className="w-4 h-4 text-arb-text-dim" />;
    case "png":
    case "jpg":
    case "jpeg":
    case "gif":
    case "svg":
      return <Image className="w-4 h-4 text-pink-400" />;
    case "rs":
      return <FileCode className="w-4 h-4 text-orange-400" />;
    case "go":
      return <FileCode className="w-4 h-4 text-cyan-400" />;
    default:
      return <File className="w-4 h-4 text-arb-text-muted" />;
  }
}

interface TreeItemProps {
  node: FileTreeNode;
  depth: number;
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
  expandedFolders: Set<string>;
  toggleFolder: (path: string) => void;
}

function TreeItem({
  node,
  depth,
  selectedFile,
  onFileSelect,
  expandedFolders,
  toggleFolder,
}: TreeItemProps) {
  const isFolder = node.type === "folder";
  const isSelected = selectedFile === node.path;
  const isOpen = expandedFolders.has(node.path);

  const handleClick = () => {
    if (isFolder) {
      toggleFolder(node.path);
    } else {
      onFileSelect(node.path);
    }
  };

  return (
    <div>
      <button
        onClick={handleClick}
        className={clsx(
          "w-full flex items-center gap-1.5 px-2 py-1 text-sm text-left tree-item rounded-md",
          isSelected
            ? "bg-arb-accent/10 text-arb-accent"
            : "hover:bg-arb-hover text-arb-text"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {/* Expand/collapse chevron for folders */}
        {isFolder ? (
          <span className="w-4 h-4 flex items-center justify-center text-arb-text-muted">
            {isOpen ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </span>
        ) : (
          <span className="w-4" />
        )}

        {/* Icon */}
        {isFolder ? (
          isOpen ? (
            <FolderOpen className="w-4 h-4 text-arb-accent" />
          ) : (
            <Folder className="w-4 h-4 text-arb-accent-dim" />
          )
        ) : (
          getFileIcon(node)
        )}

        {/* Name */}
        <span className="truncate">{node.name}</span>
      </button>

      {/* Children */}
      {isFolder && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
              expandedFolders={expandedFolders}
              toggleFolder={toggleFolder}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FileTreeProps {
  onFileSelect: (path: string | null) => void;
  selectedFile: string | null;
  onImportClick: () => void;
}

export function FileTree({ onFileSelect, selectedFile, onImportClick }: FileTreeProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { 
    currentProject, 
    currentSnapshot, 
    fileTree, 
    expandedFolders, 
    toggleFolder,
    setFileTree 
  } = useAppStore();

  // Auto-expand first two levels
  useEffect(() => {
    if (fileTree.length > 0 && expandedFolders.size === 0) {
      fileTree.forEach((node) => {
        if (node.type === "folder") {
          toggleFolder(node.path);
        }
      });
    }
  }, [fileTree, expandedFolders.size, toggleFolder]);

  const handleRefresh = async () => {
    if (!currentSnapshot) return;
    setIsRefreshing(true);
    try {
      const tree = await api.getFileTree(currentSnapshot.id);
      setFileTree(tree);
    } catch (err) {
      console.error("Failed to refresh tree:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Filter tree based on search
  const filterTree = (nodes: FileTreeNode[], query: string): FileTreeNode[] => {
    if (!query) return nodes;
    
    return nodes.reduce<FileTreeNode[]>((acc, node) => {
      if (node.name.toLowerCase().includes(query.toLowerCase())) {
        acc.push(node);
      } else if (node.children) {
        const filteredChildren = filterTree(node.children, query);
        if (filteredChildren.length > 0) {
          acc.push({ ...node, children: filteredChildren });
        }
      }
      return acc;
    }, []);
  };

  const displayTree = filterTree(fileTree, searchQuery);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-arb-border">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-medium text-arb-text-dim uppercase tracking-wider">
              Explorer
            </h2>
            {currentProject && (
              <p className="text-xs text-arb-text-muted truncate mt-0.5">
                {currentProject.name}
              </p>
            )}
          </div>
          <div className="flex items-center gap-1">
            {currentSnapshot && (
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="p-1.5 rounded hover:bg-arb-surface transition-colors"
                title="Refresh"
              >
                <RefreshCw
                  className={clsx(
                    "w-3.5 h-3.5 text-arb-text-dim",
                    isRefreshing && "animate-spin"
                  )}
                />
              </button>
            )}
            <button
              onClick={onImportClick}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded bg-arb-surface hover:bg-arb-hover border border-arb-border transition-colors"
            >
              <Plus className="w-3 h-3" />
              Import
            </button>
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-arb-text-muted" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-8 pl-8 pr-3 bg-arb-surface border border-arb-border rounded-md text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 transition-all"
          />
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {displayTree.length > 0 ? (
          displayTree.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              depth={0}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
              expandedFolders={expandedFolders}
              toggleFolder={toggleFolder}
            />
          ))
        ) : currentProject ? (
          <div className="text-center py-8 text-arb-text-muted text-sm">
            {searchQuery ? "No matching files" : "No files indexed yet"}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-arb-text-muted text-sm mb-3">No project loaded</p>
            <button
              onClick={onImportClick}
              className="flex items-center gap-2 mx-auto px-3 py-1.5 text-sm bg-arb-accent hover:bg-arb-accent/80 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              Import Project
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      {currentSnapshot && (
        <div className="p-3 border-t border-arb-border text-xs text-arb-text-muted">
          <div className="flex justify-between">
            <span>{currentSnapshot.file_count} files</span>
            <span>{currentSnapshot.symbol_count} symbols</span>
          </div>
        </div>
      )}
    </div>
  );
}
