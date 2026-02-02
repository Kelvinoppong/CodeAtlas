"use client";

import { useEffect } from "react";

/**
 * Initialize appearance settings from localStorage on app load.
 * This component should be placed in the root layout.
 */
export function AppearanceProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Apply saved theme
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);
    
    // Apply saved accent color
    const savedAccent = localStorage.getItem("accent") || "purple";
    document.documentElement.setAttribute("data-accent", savedAccent);
  }, []);

  return <>{children}</>;
}
