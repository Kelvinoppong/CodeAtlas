"use client";

import { useState } from "react";
import { Loader2, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { useAppStore } from "@/lib/store";
import api, { IS_DEMO_MODE } from "@/lib/api";

// Simple graph viewer without ReactFlow for demo/static builds
export function GraphViewerSimple() {
  const { currentSnapshot, setSelectedFile } = useAppStore();
  const [loading, setLoading] = useState(false);

  // Demo nodes for display
  const demoNodes = [
    { id: "1", label: "page.tsx", x: 200, y: 50, type: "file" },
    { id: "2", label: "Header.tsx", x: 100, y: 150, type: "component" },
    { id: "3", label: "FileTree.tsx", x: 300, y: 150, type: "component" },
    { id: "4", label: "api.ts", x: 100, y: 250, type: "lib" },
    { id: "5", label: "store.ts", x: 300, y: 250, type: "lib" },
  ];

  const demoEdges = [
    { from: "1", to: "2" },
    { from: "1", to: "3" },
    { from: "2", to: "4" },
    { from: "3", to: "5" },
  ];

  const getNodeColor = (type: string) => {
    switch (type) {
      case "file": return "from-purple-400 to-purple-600";
      case "component": return "from-blue-400 to-blue-600";
      case "lib": return "from-green-400 to-green-600";
      default: return "from-gray-400 to-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-arb-accent animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-arb-bg overflow-hidden">
      {/* Background grid */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, #2a2a3a 1px, transparent 1px),
            linear-gradient(to bottom, #2a2a3a 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      {/* SVG for edges */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="#a78bfa"
            />
          </marker>
        </defs>
        {demoEdges.map((edge, i) => {
          const fromNode = demoNodes.find(n => n.id === edge.from);
          const toNode = demoNodes.find(n => n.id === edge.to);
          if (!fromNode || !toNode) return null;
          
          return (
            <line
              key={i}
              x1={fromNode.x + 40}
              y1={fromNode.y + 40}
              x2={toNode.x + 40}
              y2={toNode.y}
              stroke="#a78bfa"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
              opacity="0.6"
            />
          );
        })}
      </svg>

      {/* Nodes */}
      {demoNodes.map((node) => (
        <div
          key={node.id}
          className="absolute cursor-pointer group"
          style={{ left: node.x, top: node.y }}
          onClick={() => setSelectedFile(`src/${node.label}`)}
        >
          <div
            className={`w-20 h-20 rounded-lg bg-gradient-to-br ${getNodeColor(node.type)} 
              shadow-lg transform rotate-45 group-hover:scale-110 transition-transform
              border-2 border-white/20`}
            style={{
              boxShadow: "0 0 20px rgba(167, 139, 250, 0.4)",
            }}
          />
          <div className="absolute top-24 left-1/2 -translate-x-1/2 whitespace-nowrap">
            <span className="text-xs text-arb-text font-medium bg-arb-panel/80 px-2 py-1 rounded">
              {node.label}
            </span>
          </div>
        </div>
      ))}

      {/* Controls */}
      <div className="absolute bottom-4 left-4 flex gap-2">
        <button className="p-2 bg-arb-panel border border-arb-border rounded-lg hover:bg-arb-hover">
          <ZoomIn className="w-4 h-4 text-arb-text-dim" />
        </button>
        <button className="p-2 bg-arb-panel border border-arb-border rounded-lg hover:bg-arb-hover">
          <ZoomOut className="w-4 h-4 text-arb-text-dim" />
        </button>
        <button className="p-2 bg-arb-panel border border-arb-border rounded-lg hover:bg-arb-hover">
          <Maximize2 className="w-4 h-4 text-arb-text-dim" />
        </button>
      </div>

      {/* Info overlay for demo */}
      {IS_DEMO_MODE && (
        <div className="absolute top-4 right-4 bg-arb-panel/90 border border-arb-border rounded-lg p-3 max-w-xs">
          <p className="text-xs text-arb-text-dim">
            📊 <span className="text-arb-text font-medium">Demo Graph</span>
            <br />
            Run CodeAtlas locally for interactive dependency visualization with ReactFlow.
          </p>
        </div>
      )}
    </div>
  );
}
