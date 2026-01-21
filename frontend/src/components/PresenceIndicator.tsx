"use client";

import { useEffect, useRef, useState } from "react";
import { Users, Circle } from "lucide-react";
import clsx from "clsx";
import { UserPresence } from "@/lib/api";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { useAuthStore } from "@/lib/authStore";

interface PresenceIndicatorProps {
  projectId: string;
}

export function PresenceIndicator({ projectId }: PresenceIndicatorProps) {
  const [users, setUsers] = useState<UserPresence[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const { selectedFile } = useAppStore();
  const { user, isAuthenticated } = useAuthStore();
  
  useEffect(() => {
    if (!isAuthenticated || !projectId) return;
    
    const token = api.getAccessToken();
    if (!token) return;
    
    // Connect to WebSocket
    const wsUrl = `ws://localhost:8000/ws/${projectId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log("WebSocket connected");
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case "room_state":
          setUsers(data.users);
          break;
        case "user_joined":
          setUsers(data.users);
          break;
        case "user_left":
          setUsers(data.users);
          break;
        case "presence_update":
          setUsers((prev) => 
            prev.map((u) => 
              u.user_id === data.user.user_id ? data.user : u
            )
          );
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
    
    ws.onclose = () => {
      console.log("WebSocket closed");
    };
    
    return () => {
      ws.close();
    };
  }, [isAuthenticated, projectId]);
  
  // Send cursor position updates
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && selectedFile) {
      wsRef.current.send(JSON.stringify({
        type: "file_open",
        file: selectedFile,
      }));
    }
  }, [selectedFile]);
  
  // Filter out current user
  const otherUsers = users.filter((u) => u.user_id !== user?.id);
  
  if (!isAuthenticated || otherUsers.length === 0) {
    return null;
  }
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-arb-surface border border-arb-border hover:border-arb-accent/50 transition-colors"
      >
        <Users className="w-4 h-4 text-arb-text-dim" />
        
        {/* Avatar stack */}
        <div className="flex -space-x-2">
          {otherUsers.slice(0, 3).map((user) => (
            <div
              key={user.user_id}
              className="w-6 h-6 rounded-full border-2 border-arb-panel flex items-center justify-center text-xs text-white font-medium"
              style={{ backgroundColor: user.color }}
              title={user.user_name}
            >
              {user.user_name.charAt(0).toUpperCase()}
            </div>
          ))}
          {otherUsers.length > 3 && (
            <div className="w-6 h-6 rounded-full border-2 border-arb-panel bg-arb-surface flex items-center justify-center text-xs text-arb-text-dim">
              +{otherUsers.length - 3}
            </div>
          )}
        </div>
        
        <span className="text-xs text-arb-text-dim">
          {otherUsers.length} online
        </span>
      </button>
      
      {/* Expanded list */}
      {isExpanded && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-arb-panel border border-arb-border rounded-xl shadow-xl overflow-hidden animate-scale-in z-50">
          <div className="p-3 border-b border-arb-border">
            <h3 className="text-sm font-medium text-arb-text">Online Users</h3>
          </div>
          
          <div className="max-h-64 overflow-y-auto p-2">
            {otherUsers.map((user) => (
              <div
                key={user.user_id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-arb-surface transition-colors"
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-sm text-white font-medium relative"
                  style={{ backgroundColor: user.color }}
                >
                  {user.user_name.charAt(0).toUpperCase()}
                  <Circle
                    className="w-3 h-3 absolute -bottom-0.5 -right-0.5 fill-emerald-400 text-arb-panel"
                    strokeWidth={3}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-arb-text truncate">
                    {user.user_name}
                  </p>
                  {user.current_file && (
                    <p className="text-xs text-arb-text-dim truncate">
                      Viewing {user.current_file.split("/").pop()}
                    </p>
                  )}
                </div>
                
                {/* Cursor indicator */}
                {user.cursor_line && (
                  <span className="text-xs text-arb-text-muted">
                    L{user.cursor_line}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
