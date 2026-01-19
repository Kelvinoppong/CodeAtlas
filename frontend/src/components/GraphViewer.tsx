"use client";

import { useCallback, useEffect, useState } from "react";
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

// Custom diamond node matching the screenshot
function DiamondNode({ data }: { data: { label: string; type?: string } }) {
  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="opacity-0" />
      <div
        className="w-16 h-16 bg-gradient-to-br from-arb-node to-arb-accent rounded-lg diamond shadow-glow cursor-pointer hover:scale-110 transition-transform"
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

const nodeTypes = {
  diamond: DiamondNode,
};

// Demo graph matching the screenshot's diamond pattern
const initialNodes: Node[] = [
  // Top row
  {
    id: "1",
    type: "diamond",
    position: { x: 200, y: 0 },
    data: { label: "main" },
  },
  // Second row
  {
    id: "2",
    type: "diamond",
    position: { x: 120, y: 80 },
    data: { label: "init" },
  },
  {
    id: "3",
    type: "diamond",
    position: { x: 280, y: 80 },
    data: { label: "game" },
  },
  // Third row
  {
    id: "4",
    type: "diamond",
    position: { x: 40, y: 160 },
    data: { label: "board" },
  },
  {
    id: "5",
    type: "diamond",
    position: { x: 120, y: 160 },
    data: { label: "mines" },
  },
  {
    id: "6",
    type: "diamond",
    position: { x: 200, y: 160 },
    data: { label: "cells" },
  },
  {
    id: "7",
    type: "diamond",
    position: { x: 280, y: 160 },
    data: { label: "click" },
  },
  {
    id: "8",
    type: "diamond",
    position: { x: 360, y: 160 },
    data: { label: "reveal" },
  },
  // Fourth row
  {
    id: "9",
    type: "diamond",
    position: { x: 80, y: 240 },
    data: { label: "check" },
  },
  {
    id: "10",
    type: "diamond",
    position: { x: 160, y: 240 },
    data: { label: "count" },
  },
  {
    id: "11",
    type: "diamond",
    position: { x: 240, y: 240 },
    data: { label: "flag" },
  },
  {
    id: "12",
    type: "diamond",
    position: { x: 320, y: 240 },
    data: { label: "win" },
  },
  // Fifth row
  {
    id: "13",
    type: "diamond",
    position: { x: 120, y: 320 },
    data: { label: "adj" },
  },
  {
    id: "14",
    type: "diamond",
    position: { x: 200, y: 320 },
    data: { label: "safe" },
  },
  {
    id: "15",
    type: "diamond",
    position: { x: 280, y: 320 },
    data: { label: "lose" },
  },
  // Bottom row
  {
    id: "16",
    type: "diamond",
    position: { x: 200, y: 400 },
    data: { label: "end" },
  },
];

const initialEdges: Edge[] = [
  // From main
  { id: "e1-2", source: "1", target: "2", animated: true },
  { id: "e1-3", source: "1", target: "3", animated: true },
  // From init
  { id: "e2-4", source: "2", target: "4" },
  { id: "e2-5", source: "2", target: "5" },
  // From game
  { id: "e3-6", source: "3", target: "6" },
  { id: "e3-7", source: "3", target: "7" },
  { id: "e3-8", source: "3", target: "8" },
  // From board/mines
  { id: "e4-9", source: "4", target: "9" },
  { id: "e5-10", source: "5", target: "10" },
  // From cells/click
  { id: "e6-11", source: "6", target: "11" },
  { id: "e7-11", source: "7", target: "11" },
  { id: "e8-12", source: "8", target: "12" },
  // To bottom
  { id: "e9-13", source: "9", target: "13" },
  { id: "e10-14", source: "10", target: "14" },
  { id: "e11-14", source: "11", target: "14" },
  { id: "e12-15", source: "12", target: "15" },
  // To end
  { id: "e14-16", source: "14", target: "16" },
  { id: "e15-16", source: "15", target: "16" },
].map((edge) => ({
  ...edge,
  style: { stroke: "#a78bfa", strokeWidth: 2 },
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: "#a78bfa",
  },
}));

export function GraphViewer() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="h-full w-full bg-arb-bg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
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
          style={{
            button: {
              backgroundColor: "#12121a",
              borderColor: "#2a2a3a",
              color: "#e4e4eb",
            },
          }}
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
