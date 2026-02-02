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
        // Deep dark theme inspired by the screenshot
        "arb-bg": "#0a0a0f",
        "arb-panel": "#12121a",
        "arb-surface": "#1a1a24",
        "arb-border": "#2a2a3a",
        "arb-hover": "#252532",
        // Accent - soft purple/lavender from the graph nodes
        "arb-accent": "#a78bfa",
        "arb-accent-dim": "#7c5ccc",
        // Text hierarchy
        "arb-text": "#e4e4eb",
        "arb-text-dim": "#8888a0",
        "arb-text-muted": "#5a5a70",
        // Graph node colors
        "arb-node": "#c4b5fd",
        "arb-node-glow": "rgba(167, 139, 250, 0.4)",
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
        "glow": "0 0 20px rgba(167, 139, 250, 0.3)",
        "glow-lg": "0 0 40px rgba(167, 139, 250, 0.4)",
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
