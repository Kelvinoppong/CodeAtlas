import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme colors using CSS variables for dynamic theming
        "arb-bg": "var(--bg-color)",
        "arb-panel": "var(--panel-color)",
        "arb-surface": "var(--surface-color)",
        "arb-border": "var(--border-color)",
        "arb-hover": "var(--hover-color)",
        // Accent - using CSS variable for dynamic color
        "arb-accent": "var(--accent-color)",
        "arb-accent-dim": "var(--accent-color-dim)",
        // Text hierarchy
        "arb-text": "var(--text-color)",
        "arb-text-dim": "var(--text-dim)",
        "arb-text-muted": "var(--text-muted)",
        // Graph node colors (using accent)
        "arb-node": "var(--accent-color)",
        "arb-node-glow": "rgba(var(--accent-color-rgb), 0.4)",
        // Success/error states
        "arb-success": "#4ade80",
        "arb-error": "#f87171",
        "arb-warning": "#fbbf24",
      },
      fontFamily: {
        sans: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "glow": "0 0 20px rgba(var(--accent-color-rgb), 0.3)",
        "glow-lg": "0 0 40px rgba(var(--accent-color-rgb), 0.4)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
