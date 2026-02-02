import type { Metadata } from "next";
import "./globals.css";
import { AppearanceProvider } from "@/components/AppearanceProvider";

export const metadata: Metadata = {
  title: "CodeAtlas — Code Analysis Platform",
  description:
    "A code analysis platform that uses your file tree to provide comprehensive codebase context, AI file modification, branching tree tools, and stunning visualizations.",
};

// Script to apply theme immediately to prevent flash
const themeScript = `
  (function() {
    try {
      var theme = localStorage.getItem('theme') || 'dark';
      var accent = localStorage.getItem('accent') || 'purple';
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.setAttribute('data-accent', accent);
    } catch (e) {}
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-arb-bg text-arb-text antialiased">
        <AppearanceProvider>{children}</AppearanceProvider>
      </body>
    </html>
  );
}
