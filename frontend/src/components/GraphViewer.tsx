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
} from "reactflow";
import "reactflow/dist/style.css";
import { Loader2 } from "lucide-react";
import { useAppStore } from "@/lib/store";
import api, { GraphNode, GraphEdge } from "@/lib/api";

// Custom diamond node matching the screenshot
function DiamondNode({ data }: { data: { label: string; type?: string } }) {
  const getColor = () => {
    switch (data.type) {
      case "class":
        return "from-yellow-400 to-amber-500";
      case "function":
      case "method":
        return "from-blue-400 to-indigo-500";
      case "file":
        return "from-arb-node to-arb-accent";
      default:
        return "from-arb-node to-arb-accent";
    }
  };

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <div
        className={`w-16 h-16 bg-gradient-to-br ${getColor()} rounded-lg diamond shadow-glow cursor-pointer hover:scale-110 transition-transform`}
        style={{
          boxShadow: "0 0 30px rgba(196, 181, 253, 0.4)",
        }}
      >
        <div className="absolute inset-0 flex items-center justify-center diamond-content">
          <span className="text-xs font-medium text-arb-bg truncate max-w-[50px]">
            {data.label}
          </span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
      <Handle type="source" position={Position.Left} className="opacity-0" />
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  );
}

// Standard node for larger graphs
function StandardNode({ data }: { data: { label: string; type?: string } }) {
  const getBgColor = () => {
    switch (data.type) {
      case "class":
        return "bg-yellow-500/20 border-yellow-500/50";
      case "function":
      case "method":
        return "bg-blue-500/20 border-blue-500/50";
      case "file":
        return "bg-arb-accent/20 border-arb-accent/50";
      default:
        return "bg-arb-surface border-arb-border";
    }
  };

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <div
        className={`px-3 py-2 rounded-lg border ${getBgColor()} cursor-pointer hover:scale-105 transition-transform`}
      >
        <span className="text-xs font-medium text-arb-text">
          {data.label}
        </span>
      </div>
      <Handle type="source" position={Position.Bottom} className="opacity-0" />
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
  style: { stroke: "#a78bfa", strokeWidth: 2 },
  markerEnd: { type: MarkerType.ArrowClosed, color: "#a78bfa" },
}));

function layoutNodes(graphNodes: GraphNode[]): Node[] {
  // Simple hierarchical layout
  const levels: Map<string, number> = new Map();
  const nodeMap = new Map(graphNodes.map((n) => [n.id, n]));
  
  // Calculate levels (simplified)
  graphNodes.forEach((node, i) => {
    if (node.type === "file") {
      levels.set(node.id, 0);
    } else if (node.type === "class") {
      levels.set(node.id, 1);
    } else {
      levels.set(node.id, 2);
    }
  });

  // Position nodes
  const levelCounts: Map<number, number> = new Map();
  
  return graphNodes.map((node) => {
    const level = levels.get(node.id) || 0;
    const count = levelCounts.get(level) || 0;
    levelCounts.set(level, count + 1);

    return {
      id: node.id,
      type: graphNodes.length > 20 ? "standard" : "diamond",
      position: {
        x: count * 100 + 50,
        y: level * 100 + 50,
      },
      data: {
        label: node.label,
        type: node.type,
      },
    };
  });
}

function layoutEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map((edge, i) => ({
    id: `e-${i}`,
    source: edge.source,
    target: edge.target,
    style: { stroke: "#a78bfa", strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#a78bfa" },
    animated: edge.type === "contains",
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
        fitViewOptions={{ padding: 0.3 }}
        defaultEdgeOptions={{
          style: { stroke: "#a78bfa", strokeWidth: 2 },
        }}
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
