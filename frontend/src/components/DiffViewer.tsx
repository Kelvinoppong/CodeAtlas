"use client";

import { useMemo } from "react";
import { Plus, Minus, FileText } from "lucide-react";
import clsx from "clsx";

interface DiffViewerProps {
  diff: string;
  filePath: string;
  language?: string;
  showHeader?: boolean;
}

interface DiffLine {
  type: "context" | "addition" | "deletion" | "header" | "range";
  content: string;
  oldLineNum?: number;
  newLineNum?: number;
}

function parseDiff(diff: string): DiffLine[] {
  const lines = diff.split("\n");
  const result: DiffLine[] = [];
  
  let oldLine = 0;
  let newLine = 0;
  
  for (const line of lines) {
    if (line.startsWith("@@")) {
      // Parse range header: @@ -start,count +start,count @@
      const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
      if (match) {
        oldLine = parseInt(match[1], 10);
        newLine = parseInt(match[2], 10);
      }
      result.push({ type: "range", content: line });
    } else if (line.startsWith("---") || line.startsWith("+++")) {
      result.push({ type: "header", content: line });
    } else if (line.startsWith("-")) {
      result.push({
        type: "deletion",
        content: line.slice(1),
        oldLineNum: oldLine++,
      });
    } else if (line.startsWith("+")) {
      result.push({
        type: "addition",
        content: line.slice(1),
        newLineNum: newLine++,
      });
    } else if (line.startsWith(" ") || line === "") {
      result.push({
        type: "context",
        content: line.slice(1) || "",
        oldLineNum: oldLine++,
        newLineNum: newLine++,
      });
    }
  }
  
  return result;
}

export function DiffViewer({ diff, filePath, language, showHeader = true }: DiffViewerProps) {
  const parsedLines = useMemo(() => parseDiff(diff), [diff]);
  
  const stats = useMemo(() => {
    let additions = 0;
    let deletions = 0;
    for (const line of parsedLines) {
      if (line.type === "addition") additions++;
      if (line.type === "deletion") deletions++;
    }
    return { additions, deletions };
  }, [parsedLines]);
  
  if (!diff || diff.trim() === "") {
    return (
      <div className="flex items-center justify-center p-8 text-arb-text-muted">
        <p>No changes</p>
      </div>
    );
  }
  
  return (
    <div className="font-mono text-sm">
      {/* File header */}
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-2 bg-arb-surface border-b border-arb-border sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-arb-accent" />
            <span className="text-arb-text font-medium">{filePath}</span>
            {language && (
              <span className="text-xs px-2 py-0.5 rounded bg-arb-bg text-arb-text-dim">
                {language}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1 text-emerald-400">
              <Plus className="w-3 h-3" />
              {stats.additions}
            </span>
            <span className="flex items-center gap-1 text-rose-400">
              <Minus className="w-3 h-3" />
              {stats.deletions}
            </span>
          </div>
        </div>
      )}
      
      {/* Diff content */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <tbody>
            {parsedLines.map((line, idx) => {
              if (line.type === "header") {
                return (
                  <tr key={idx} className="bg-arb-bg/50">
                    <td colSpan={4} className="px-4 py-1 text-arb-text-muted text-xs">
                      {line.content}
                    </td>
                  </tr>
                );
              }
              
              if (line.type === "range") {
                return (
                  <tr key={idx} className="bg-arb-surface/50">
                    <td colSpan={4} className="px-4 py-2 text-arb-accent text-xs font-medium">
                      {line.content}
                    </td>
                  </tr>
                );
              }
              
              return (
                <tr
                  key={idx}
                  className={clsx(
                    "hover:brightness-110 transition-all",
                    line.type === "addition" && "bg-emerald-500/10",
                    line.type === "deletion" && "bg-rose-500/10",
                    line.type === "context" && "bg-transparent"
                  )}
                >
                  {/* Old line number */}
                  <td className="w-12 text-right px-2 py-0 text-arb-text-muted text-xs select-none border-r border-arb-border/30">
                    {line.type !== "addition" && line.oldLineNum}
                  </td>
                  
                  {/* New line number */}
                  <td className="w-12 text-right px-2 py-0 text-arb-text-muted text-xs select-none border-r border-arb-border/30">
                    {line.type !== "deletion" && line.newLineNum}
                  </td>
                  
                  {/* Change indicator */}
                  <td className="w-6 text-center py-0 select-none">
                    {line.type === "addition" && (
                      <span className="text-emerald-400 font-bold">+</span>
                    )}
                    {line.type === "deletion" && (
                      <span className="text-rose-400 font-bold">−</span>
                    )}
                  </td>
                  
                  {/* Content */}
                  <td className="px-2 py-0.5 whitespace-pre">
                    <span
                      className={clsx(
                        line.type === "addition" && "text-emerald-300",
                        line.type === "deletion" && "text-rose-300",
                        line.type === "context" && "text-arb-text-dim"
                      )}
                    >
                      {line.content || " "}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
