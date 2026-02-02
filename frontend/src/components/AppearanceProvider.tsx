"use client";

import { useEffect } from "react";

/**
 * Syncs appearance settings and listens for changes.
 * The initial theme is applied via inline script in layout.tsx to prevent flash.
 */
export function AppearanceProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Sync body attributes with html (for full CSS coverage)
    const syncAttributes = () => {
      const theme = document.documentElement.getAttribute("data-theme");
      const accent = document.documentElement.getAttribute("data-accent");
      if (theme) document.body.setAttribute("data-theme", theme);
      if (accent) document.body.setAttribute("data-accent", accent);
    };
    
    syncAttributes();
    
    // Watch for attribute changes on html element
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === "data-theme" || mutation.attributeName === "data-accent") {
          syncAttributes();
        }
      });
    });
    
    observer.observe(document.documentElement, { attributes: true });
    
    return () => observer.disconnect();
  }, []);

  return <>{children}</>;
}
