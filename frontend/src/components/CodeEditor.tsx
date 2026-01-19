"use client";

import { useEffect, useState } from "react";
import { FileCode, Copy, Download, ExternalLink, Loader2, Check } from "lucide-react";
import clsx from "clsx";
import { useAppStore } from "@/lib/store";

// Demo code for when no file is selected
const demoCode = `import itertools
import random

class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):
        
        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()
        
        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)
        
        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(self.height)
            j = random.randrange(self.width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True
        
        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")`;

interface CodeEditorProps {
  selectedFile: string | null;
}

// Simple syntax highlighting
function highlightCode(code: string, language?: string): React.ReactNode[] {
  const lines = code.split("\n");
  const keywords: Record<string, string[]> = {
    python: [
      "import", "from", "class", "def", "return", "if", "else", "elif",
      "for", "while", "in", "not", "and", "or", "True", "False", "None",
      "self", "range", "set", "print", "len", "try", "except", "finally",
      "with", "as", "yield", "lambda", "pass", "break", "continue",
    ],
    javascript: [
      "import", "export", "from", "const", "let", "var", "function",
      "return", "if", "else", "for", "while", "class", "extends",
      "new", "this", "async", "await", "try", "catch", "throw",
      "true", "false", "null", "undefined",
    ],
    typescript: [
      "import", "export", "from", "const", "let", "var", "function",
      "return", "if", "else", "for", "while", "class", "extends",
      "new", "this", "async", "await", "try", "catch", "throw",
      "true", "false", "null", "undefined", "interface", "type",
      "enum", "implements", "private", "public", "protected",
    ],
  };

  const langKeywords = keywords[language || ""] || keywords.python;

  return lines.map((line, i) => {
    let highlighted = line;

    // Comments
    const commentPatterns = [
      { pattern: /#.*$/, replacement: '<span class="text-arb-text-muted">$&</span>' },
      { pattern: /\/\/.*$/, replacement: '<span class="text-arb-text-muted">$&</span>' },
    ];

    for (const { pattern, replacement } of commentPatterns) {
      highlighted = highlighted.replace(pattern, replacement);
    }

    // Strings (triple quotes, single, double)
    if (highlighted.includes('"""') || highlighted.includes("'''")) {
      highlighted = `<span class="text-emerald-400">${line}</span>`;
    } else {
      highlighted = highlighted.replace(
        /(["'])(?:(?=(\\?))\2.)*?\1/g,
        '<span class="text-emerald-400">$&</span>'
      );
    }

    // Keywords
    langKeywords.forEach((kw) => {
      const regex = new RegExp(`\\b${kw}\\b`, "g");
      highlighted = highlighted.replace(
        regex,
        `<span class="text-arb-accent">${kw}</span>`
      );
    });

    // Numbers
    highlighted = highlighted.replace(
      /\b(\d+)\b/g,
      '<span class="text-amber-400">$1</span>'
    );

    // Function definitions
    highlighted = highlighted.replace(
      /def\s+(\w+)/g,
      'def <span class="text-blue-400">$1</span>'
    );
    highlighted = highlighted.replace(
      /function\s+(\w+)/g,
      'function <span class="text-blue-400">$1</span>'
    );

    // Class definitions
    highlighted = highlighted.replace(
      /class\s+(\w+)/g,
      'class <span class="text-yellow-400">$1</span>'
    );

    return (
      <div key={i} className="table-row hover:bg-arb-hover/30 transition-colors">
        <span className="table-cell pr-4 text-right text-arb-text-muted select-none w-12">
          {i + 1}
        </span>
        <span
          className="table-cell"
          dangerouslySetInnerHTML={{ __html: highlighted || "&nbsp;" }}
        />
      </div>
    );
  });
}

export function CodeEditor({ selectedFile }: CodeEditorProps) {
  const { fileContent, isLoadingFile, currentSnapshot } = useAppStore();
  const [copied, setCopied] = useState(false);

  const code = fileContent?.content || (!currentSnapshot ? demoCode : "");
  const language = fileContent?.language || "python";
  const fileName = selectedFile || "minesweeper.py";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-arb-border bg-arb-surface/50">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium">
            {fileName.split("/").pop()}
          </span>
          <span className="text-xs text-arb-text-muted truncate max-w-[200px]">
            {fileName}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {isLoadingFile && (
            <Loader2 className="w-4 h-4 text-arb-accent animate-spin mr-2" />
          )}
          <button
            onClick={handleCopy}
            className="p-1.5 rounded hover:bg-arb-hover transition-colors"
            title="Copy"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-arb-success" />
            ) : (
              <Copy className="w-3.5 h-3.5 text-arb-text-dim" />
            )}
          </button>
          <button
            className="p-1.5 rounded hover:bg-arb-hover transition-colors"
            title="Download"
          >
            <Download className="w-3.5 h-3.5 text-arb-text-dim" />
          </button>
          <button
            className="p-1.5 rounded hover:bg-arb-hover transition-colors"
            title="Open external"
          >
            <ExternalLink className="w-3.5 h-3.5 text-arb-text-dim" />
          </button>
        </div>
      </div>

      {/* Code Content */}
      <div className="flex-1 overflow-auto p-4 font-mono text-sm leading-6">
        {code ? (
          <div className="table w-full">{highlightCode(code, language)}</div>
        ) : isLoadingFile ? (
          <div className="flex items-center justify-center h-full text-arb-text-muted">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-arb-text-muted">
            Select a file to view its contents
          </div>
        )}
      </div>

      {/* Status bar */}
      {fileContent && (
        <div className="flex-shrink-0 px-4 py-1.5 border-t border-arb-border bg-arb-surface/30 text-xs text-arb-text-muted flex items-center justify-between">
          <span>{language || "plain text"}</span>
          <span>{fileContent.line_count} lines</span>
        </div>
      )}
    </div>
  );
}
