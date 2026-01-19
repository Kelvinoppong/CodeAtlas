"use client";

import { useEffect, useState } from "react";
import { FileCode, Copy, Download, ExternalLink } from "lucide-react";
import clsx from "clsx";

// Demo code matching the screenshot's Python minesweeper
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
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """
        count = 0
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                if (i, j) == cell:
                    continue
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1
        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines`;

interface CodeEditorProps {
  selectedFile: string | null;
}

// Simple syntax highlighting for Python
function highlightPython(code: string): React.ReactNode[] {
  const lines = code.split("\n");
  const keywords = [
    "import",
    "from",
    "class",
    "def",
    "return",
    "if",
    "else",
    "elif",
    "for",
    "while",
    "in",
    "not",
    "and",
    "or",
    "True",
    "False",
    "None",
    "self",
    "range",
    "set",
    "print",
    "len",
  ];

  return lines.map((line, i) => {
    let highlighted = line;

    // Comments
    if (line.includes("#")) {
      const idx = line.indexOf("#");
      const before = line.slice(0, idx);
      const comment = line.slice(idx);
      highlighted = before + `<span class="text-arb-text-muted">${comment}</span>`;
    }

    // Strings (triple quotes)
    if (line.includes('"""')) {
      highlighted = `<span class="text-emerald-400">${line}</span>`;
    }

    // Keywords
    keywords.forEach((kw) => {
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
  const [code, setCode] = useState(demoCode);
  const fileName = selectedFile || "minesweeper.py";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-arb-border bg-arb-surface/50">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-yellow-400" />
          <span className="text-sm font-medium">{fileName.split("/").pop()}</span>
          <span className="text-xs text-arb-text-muted">{fileName}</span>
        </div>
        <div className="flex items-center gap-1">
          <button className="p-1.5 rounded hover:bg-arb-hover transition-colors" title="Copy">
            <Copy className="w-3.5 h-3.5 text-arb-text-dim" />
          </button>
          <button className="p-1.5 rounded hover:bg-arb-hover transition-colors" title="Download">
            <Download className="w-3.5 h-3.5 text-arb-text-dim" />
          </button>
          <button className="p-1.5 rounded hover:bg-arb-hover transition-colors" title="Open external">
            <ExternalLink className="w-3.5 h-3.5 text-arb-text-dim" />
          </button>
        </div>
      </div>

      {/* Code Content */}
      <div className="flex-1 overflow-auto p-4 font-mono text-sm leading-6">
        <div className="table w-full">{highlightPython(code)}</div>
      </div>
    </div>
  );
}
