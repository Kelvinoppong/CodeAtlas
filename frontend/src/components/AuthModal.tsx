"use client";

import { useState } from "react";
import { X, Mail, Lock, User, Loader2, Sparkles, LogIn, UserPlus } from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "@/lib/authStore";

interface AuthModalProps {
  onClose: () => void;
  initialMode?: "login" | "register";
}

export function AuthModal({ onClose, initialMode = "login" }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, register } = useAuthStore();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        if (!name.trim()) {
          setError("Please enter your name");
          setIsLoading(false);
          return;
        }
        await register(email, password, name);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-arb-panel border border-arb-border rounded-2xl w-full max-w-md p-8 shadow-2xl animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-arb-accent to-arb-accent-dim flex items-center justify-center shadow-glow">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-display font-semibold text-arb-text">
                {mode === "login" ? "Welcome back" : "Create account"}
              </h2>
              <p className="text-sm text-arb-text-dim">
                {mode === "login" 
                  ? "Sign in to continue" 
                  : "Join CodeAtlas today"
                }
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-arb-surface transition-colors"
          >
            <X className="w-5 h-5 text-arb-text-dim" />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {mode === "register" && (
            <div>
              <label className="block text-sm font-medium text-arb-text-dim mb-2">
                Name
              </label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full h-12 pl-11 pr-4 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-2 focus:ring-arb-accent/20 transition-all"
                  disabled={isLoading}
                />
              </div>
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-arb-text-dim mb-2">
              Email
            </label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full h-12 pl-11 pr-4 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-2 focus:ring-arb-accent/20 transition-all"
                disabled={isLoading}
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-arb-text-dim mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-arb-text-muted" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "••••••••"}
                className="w-full h-12 pl-11 pr-4 bg-arb-surface border border-arb-border rounded-xl text-sm placeholder:text-arb-text-muted focus:outline-none focus:border-arb-accent/50 focus:ring-2 focus:ring-arb-accent/20 transition-all"
                disabled={isLoading}
                required
                minLength={mode === "register" ? 8 : undefined}
              />
            </div>
          </div>
          
          {/* Error */}
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-sm text-rose-400">
              {error}
            </div>
          )}
          
          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full h-12 flex items-center justify-center gap-2 bg-arb-accent hover:bg-arb-accent/80 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-medium text-white transition-all shadow-glow"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : mode === "login" ? (
              <>
                <LogIn className="w-5 h-5" />
                Sign In
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5" />
                Create Account
              </>
            )}
          </button>
        </form>
        
        {/* Toggle mode */}
        <div className="mt-6 text-center">
          <p className="text-sm text-arb-text-dim">
            {mode === "login" ? (
              <>
                Don&apos;t have an account?{" "}
                <button
                  onClick={() => setMode("register")}
                  className="text-arb-accent hover:underline font-medium"
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  onClick={() => setMode("login")}
                  className="text-arb-accent hover:underline font-medium"
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
