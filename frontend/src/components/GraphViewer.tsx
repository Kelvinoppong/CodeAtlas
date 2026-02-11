"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  MarkerType,
  Handle,
  ConnectionLineType,
} from "reactflow";
import "reactflow/dist/style.css";
import { Loader2 } from "lucide-react";
import { useAppStore } from "@/lib/store";
import api, { GraphNode, GraphEdge } from "@/lib/api";

// Custom diamond node matching the screenshot
function DiamondNode({ data }: { data: { label: string; type?: string } }) {
  const getGradient = () => {
    switch (data.type) {
      case "class":
        return "linear-gradient(135deg, #facc15 0%, #f59e0b 100%)"; // yellow to amber
      case "function":
      case "method":
        return "linear-gradient(135deg, #60a5fa 0%, #6366f1 100%)"; // blue to indigo
      case "file":
        return "linear-gradient(135deg, #fbbf24 0%, #f97316 100%)"; // amber to orange
      default:
        return "linear-gradient(135deg, #fbbf24 0%, #f97316 100%)"; // amber to orange (like screenshot)
    }
  };

  return (
    <div className="relative flex flex-col items-center">
      <Handle type="target" position={Position.Top} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <Handle type="target" position={Position.Left} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <div
        className="w-12 h-12 rounded-lg cursor-pointer hover:scale-110 transition-transform"
        style={{
          background: getGradient(),
          boxShadow: "0 0 20px rgba(251, 191, 36, 0.4)",
          transform: "rotate(45deg)",
        }}
      />
      <Handle type="source" position={Position.Bottom} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <Handle type="source" position={Position.Right} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      {/* Label below the diamond */}
      <div className="mt-2 px-2 py-1 rounded text-center max-w-[120px]" style={{ backgroundColor: "rgba(26, 26, 36, 0.8)" }}>
        <span className="text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis block" style={{ color: "#e4e4eb" }}>
          {data.label}
        </span>
        {data.type && (
          <span className="text-[10px]" style={{ color: "#8888a0" }}>{data.type}</span>
        )}
      </div>
    </div>
  );
}

// Standard node for larger graphs
function StandardNode({ data }: { data: { label: string; type?: string } }) {
  const getStyles = () => {
    switch (data.type) {
      case "class":
        return { background: "rgba(234, 179, 8, 0.2)", borderColor: "rgba(234, 179, 8, 0.5)" };
      case "function":
      case "method":
        return { background: "rgba(59, 130, 246, 0.2)", borderColor: "rgba(59, 130, 246, 0.5)" };
      case "file":
        return { background: "rgba(167, 139, 250, 0.2)", borderColor: "rgba(167, 139, 250, 0.5)" };
      default:
        return { background: "#1a1a24", borderColor: "#2a2a3a" };
    }
  };

  const getTypeIcon = () => {
    switch (data.type) {
      case "class": return "◆";
      case "function": return "ƒ";
      case "method": return "→";
      case "file": return "📄";
      default: return "•";
    }
  };

  const styles = getStyles();

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <Handle type="target" position={Position.Left} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <div
        className="px-3 py-2 rounded-lg border-2 cursor-pointer hover:scale-105 transition-all shadow-lg"
        style={{ backgroundColor: styles.background, borderColor: styles.borderColor }}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs opacity-60">{getTypeIcon()}</span>
          <span className="text-sm font-medium max-w-[150px] truncate" style={{ color: "#e4e4eb" }}>
            {data.label}
          </span>
        </div>
        {data.type && (
          <span className="text-[10px] block mt-0.5" style={{ color: "#8888a0" }}>{data.type}</span>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
      <Handle type="source" position={Position.Right} style={{ background: "#a78bfa", width: 8, height: 8, border: "none" }} />
    </div>
  );
}

const nodeTypes = {
  diamond: DiamondNode,
  standard: StandardNode,
};

// Demo nodes for when no project is loaded
const demoNodes: Node[] = [
  { id: "1", type: "diamond", position: { x: 200, y: 0 }, data: { label: "main" } },
  { id: "2", type: "diamond", position: { x: 120, y: 80 }, data: { label: "init" } },
  { id: "3", type: "diamond", position: { x: 280, y: 80 }, data: { label: "game" } },
  { id: "4", type: "diamond", position: { x: 40, y: 160 }, data: { label: "board" } },
  { id: "5", type: "diamond", position: { x: 120, y: 160 }, data: { label: "mines" } },
  { id: "6", type: "diamond", position: { x: 200, y: 160 }, data: { label: "cells" } },
  { id: "7", type: "diamond", position: { x: 280, y: 160 }, data: { label: "click" } },
  { id: "8", type: "diamond", position: { x: 360, y: 160 }, data: { label: "reveal" } },
  { id: "9", type: "diamond", position: { x: 80, y: 240 }, data: { label: "check" } },
  { id: "10", type: "diamond", position: { x: 160, y: 240 }, data: { label: "count" } },
  { id: "11", type: "diamond", position: { x: 240, y: 240 }, data: { label: "flag" } },
  { id: "12", type: "diamond", position: { x: 320, y: 240 }, data: { label: "win" } },
  { id: "13", type: "diamond", position: { x: 120, y: 320 }, data: { label: "adj" } },
  { id: "14", type: "diamond", position: { x: 200, y: 320 }, data: { label: "safe" } },
  { id: "15", type: "diamond", position: { x: 280, y: 320 }, data: { label: "lose" } },
  { id: "16", type: "diamond", position: { x: 200, y: 400 }, data: { label: "end" } },
];

const demoEdges: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true },
  { id: "e1-3", source: "1", target: "3", animated: true },
  { id: "e2-4", source: "2", target: "4" },
  { id: "e2-5", source: "2", target: "5" },
  { id: "e3-6", source: "3", target: "6" },
  { id: "e3-7", source: "3", target: "7" },
  { id: "e3-8", source: "3", target: "8" },
  { id: "e4-9", source: "4", target: "9" },
  { id: "e5-10", source: "5", target: "10" },
  { id: "e6-11", source: "6", target: "11" },
  { id: "e7-11", source: "7", target: "11" },
  { id: "e8-12", source: "8", target: "12" },
  { id: "e9-13", source: "9", target: "13" },
  { id: "e10-14", source: "10", target: "14" },
  { id: "e11-14", source: "11", target: "14" },
  { id: "e12-15", source: "12", target: "15" },
  { id: "e14-16", source: "14", target: "16" },
  { id: "e15-16", source: "15", target: "16" },
].map((edge) => ({
  ...edge,
  type: "smoothstep",
  style: { stroke: "#a78bfa", strokeWidth: 2 },
  markerEnd: { type: MarkerType.ArrowClosed, color: "#a78bfa", width: 20, height: 20 },
}));

function layoutNodes(graphNodes: GraphNode[]): Node[] {
  // Group nodes by type into levels
  const nodesByLevel: Map<number, GraphNode[]> = new Map();
  
  graphNodes.forEach((node) => {
    let level = 2; // default
    if (node.type === "file") level = 0;
    else if (node.type === "class") level = 1;
    else if (node.type === "function" || node.type === "method") level = 2;
    
    const existing = nodesByLevel.get(level) || [];
    existing.push(node);
    nodesByLevel.set(level, existing);
  });

  const results: Node[] = [];
  const nodeSpacing = 180;  // More space for labels
  const levelSpacing = 140; // More vertical space
  const maxNodesPerRow = 6; // Fewer nodes per row for readability
  
  // Sort levels and position nodes
  const sortedLevels = Array.from(nodesByLevel.keys()).sort((a, b) => a - b);
  let currentY = 50;
  
  sortedLevels.forEach((level) => {
    const nodesAtLevel = nodesByLevel.get(level) || [];
    const numNodes = nodesAtLevel.length;
    const numRows = Math.ceil(numNodes / maxNodesPerRow);
    
    nodesAtLevel.forEach((node, index) => {
      const row = Math.floor(index / maxNodesPerRow);
      const col = index % maxNodesPerRow;
      const nodesInThisRow = Math.min(maxNodesPerRow, numNodes - row * maxNodesPerRow);
      
      // Center each row
      const rowWidth = (nodesInThisRow - 1) * nodeSpacing;
      const startX = -rowWidth / 2;
      
      results.push({
        id: node.id,
        type: graphNodes.length > 30 ? "standard" : "diamond",
        position: {
          x: startX + col * nodeSpacing,
          y: currentY + row * 80,
        },
        data: {
          label: node.label,
          type: node.type,
          path: node.path,
        },
      });
    });
    
    currentY += numRows * 80 + levelSpacing;
  });

  return results;
}

function layoutEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map((edge, i) => ({
    id: `e-${i}`,
    source: edge.source,
    target: edge.target,
    type: "smoothstep",
    style: { 
      stroke: edge.type === "contains" ? "#22d3ee" : "#a78bfa", 
      strokeWidth: 2,
    },
    markerEnd: { 
      type: MarkerType.ArrowClosed, 
      color: edge.type === "contains" ? "#22d3ee" : "#a78bfa",
      width: 20,
      height: 20,
    },
    animated: edge.type === "contains",
    label: edge.type !== "imports" ? edge.type : undefined,
    labelStyle: { fill: "#9ca3af", fontSize: 10 },
    labelBgStyle: { fill: "#1a1a2e", fillOpacity: 0.8 },
  }));
}

export function GraphViewer() {
  const { currentSnapshot, selectedFile, setSelectedFile, graphData, setGraphData } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState(demoNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(demoEdges);

  // Load graph data
  useEffect(() => {
    if (!currentSnapshot) {
      setNodes(demoNodes);
      setEdges(demoEdges);
      return;
    }

    setIsLoading(true);
    api
      .getDependencyGraph(currentSnapshot.id, selectedFile || undefined)
      .then((data) => {
        setGraphData(data);
        if (data.nodes.length > 0) {
          setNodes(layoutNodes(data.nodes));
          setEdges(layoutEdges(data.edges));
        }
      })
      .catch((err) => {
        console.error("Failed to load graph:", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [currentSnapshot, selectedFile, setGraphData, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: any, node: Node) => {
      // If it's a file node, select the file
      if (node.data.type === "file" && node.data.path) {
        setSelectedFile(node.data.path);
      }
    },
    [setSelectedFile]
  );

  return (
    <div className="h-full w-full bg-arb-bg relative">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-arb-bg/80 z-10">
          <Loader2 className="w-8 h-8 text-arb-accent animate-spin" />
        </div>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3, minZoom: 0.2, maxZoom: 2 }}
        defaultEdgeOptions={{
          type: "smoothstep",
          style: { stroke: "#a78bfa", strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#a78bfa" },
        }}
        connectionLineType={ConnectionLineType.SmoothStep}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#2a2a3a" gap={20} size={1} />
        <Controls
          className="!bg-arb-panel !border-arb-border !rounded-lg !shadow-lg"
        />
        <MiniMap
          className="!bg-arb-panel !border-arb-border !rounded-lg"
          nodeColor="#a78bfa"
          maskColor="rgba(10, 10, 15, 0.8)"
        />
      </ReactFlow>
    </div>
  );
}
