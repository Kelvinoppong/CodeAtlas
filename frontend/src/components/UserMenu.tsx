"use client";

import { useState, useRef, useEffect } from "react";
import { User, LogOut, Settings, ChevronDown, Shield } from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/lib/authStore";

interface UserMenuProps {
  onLoginClick: () => void;
}

export function UserMenu({ onLoginClick }: UserMenuProps) {
  const { user, isAuthenticated, logout, isLoading } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  
  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };
  
  if (isLoading) {
    return (
      <div className="w-8 h-8 rounded-full bg-arb-surface animate-pulse" />
    );
  }
  
  if (!isAuthenticated || !user) {
    return (
      <button
        onClick={onLoginClick}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-arb-accent hover:bg-arb-accent/80 text-white text-sm font-medium transition-colors"
      >
        <User className="w-4 h-4" />
        Sign In
      </button>
    );
  }
  
  // Get initials for avatar
  const initials = user.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
  
  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          "flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors",
          isOpen ? "bg-arb-surface" : "hover:bg-arb-surface"
        )}
      >
        {/* Avatar */}
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.name}
            className="w-8 h-8 rounded-full object-cover border border-arb-border"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center text-white text-xs font-medium">
            {initials}
          </div>
        )}
        
        <span className="text-sm text-arb-text font-medium max-w-[100px] truncate hidden sm:block">
          {user.name}
        </span>
        
        <ChevronDown className={clsx(
          "w-4 h-4 text-arb-text-dim transition-transform",
          isOpen && "rotate-180"
        )} />
      </button>
      
      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-arb-panel border border-arb-border rounded-xl shadow-xl overflow-hidden animate-scale-in z-50">
          {/* User info */}
          <div className="p-4 border-b border-arb-border">
            <div className="flex items-center gap-3">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.name}
                  className="w-10 h-10 rounded-full object-cover border border-arb-border"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center text-white text-sm font-medium">
                  {initials}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-arb-text truncate">{user.name}</p>
                <p className="text-xs text-arb-text-dim truncate">{user.email}</p>
              </div>
            </div>
            
            {user.is_superuser && (
              <div className="mt-3 flex items-center gap-1.5 text-xs text-arb-accent">
                <Shield className="w-3 h-3" />
                Admin
              </div>
            )}
          </div>
          
          {/* Menu items */}
          <div className="p-2">
            <button
              onClick={() => {
                setIsOpen(false);
                // TODO: Open settings modal
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-arb-text-dim hover:text-arb-text hover:bg-arb-surface transition-colors text-sm"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
            
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-colors text-sm"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
