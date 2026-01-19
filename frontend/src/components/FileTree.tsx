"use client";

import { useState } from "react";
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
} from "lucide-react";
import clsx from "clsx";

interface FileNode {
  name: string;
  type: "file" | "folder";
  path: string;
  children?: FileNode[];
  language?: string;
}

// Demo file tree matching the screenshot structure
const demoTree: FileNode[] = [
  {
    name: "DoubleClickMe.md",
    type: "file",
    path: "/DoubleClickMe.md",
    language: "markdown",
  },
  {
    name: "minesweeper",
    type: "folder",
    path: "/minesweeper",
    children: [
      {
        name: "__pycache__",
        type: "folder",
        path: "/minesweeper/__pycache__",
        children: [
          {
            name: "minesweeper.cpython-312.pyc",
            type: "file",
            path: "/minesweeper/__pycache__/minesweeper.cpython-312.pyc",
          },
        ],
      },
      {
        name: "assets",
        type: "folder",
        path: "/minesweeper/assets",
        children: [
          {
            name: "fonts",
            type: "folder",
            path: "/minesweeper/assets/fonts",
            children: [
              {
                name: "OpenSans-Regular.ttf",
                type: "file",
                path: "/minesweeper/assets/fonts/OpenSans-Regular.ttf",
              },
            ],
          },
          {
            name: "images",
            type: "folder",
            path: "/minesweeper/assets/images",
            children: [
              {
                name: "flag.png",
                type: "file",
                path: "/minesweeper/assets/images/flag.png",
                language: "image",
              },
              {
                name: "mine.png",
                type: "file",
                path: "/minesweeper/assets/images/mine.png",
                language: "image",
              },
            ],
          },
        ],
      },
      {
        name: "minesweeper.py",
        type: "file",
        path: "/minesweeper/minesweeper.py",
        language: "python",
      },
    ],
  },
];

function getFileIcon(node: FileNode) {
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
      return <FileText className="w-4 h-4 text-arb-text-dim" />;
    case "png":
    case "jpg":
    case "jpeg":
    case "gif":
    case "svg":
      return <Image className="w-4 h-4 text-pink-400" />;
    default:
      return <File className="w-4 h-4 text-arb-text-muted" />;
  }
}

interface TreeItemProps {
  node: FileNode;
  depth: number;
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
}

function TreeItem({ node, depth, selectedFile, onFileSelect }: TreeItemProps) {
  const [isOpen, setIsOpen] = useState(depth < 2);
  const isFolder = node.type === "folder";
  const isSelected = selectedFile === node.path;

  const handleClick = () => {
    if (isFolder) {
      setIsOpen(!isOpen);
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
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FileTreeProps {
  onFileSelect: (path: string) => void;
  selectedFile: string | null;
}

export function FileTree({ onFileSelect, selectedFile }: FileTreeProps) {
  const [searchQuery, setSearchQuery] = useState("");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-arb-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-arb-text-dim uppercase tracking-wider">
            Explorer
          </h2>
          <button className="text-xs px-2 py-1 rounded bg-arb-surface hover:bg-arb-hover border border-arb-border transition-colors">
            + Import
          </button>
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-arb-text-muted" />
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-8 pl-8 pr-3 bg-arb-surface border border-arb-border rounded-md text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 transition-all"
          />
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {demoTree.map((node) => (
          <TreeItem
            key={node.path}
            node={node}
            depth={0}
            selectedFile={selectedFile}
            onFileSelect={onFileSelect}
          />
        ))}
      </div>
    </div>
  );
}
