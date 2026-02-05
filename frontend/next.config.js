/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Enable static export for GitHub Pages
  output: process.env.STATIC_EXPORT === 'true' ? 'export' : undefined,
  
  // Base path for GitHub Pages (change 'CodeAtlas' to your repo name)
  basePath: process.env.GITHUB_PAGES === 'true' ? '/CodeAtlas' : '',
  assetPrefix: process.env.GITHUB_PAGES === 'true' ? '/CodeAtlas/' : '',
  
  // Disable image optimization for static export
  images: {
    unoptimized: process.env.STATIC_EXPORT === 'true',
  },
  
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

module.exports = nextConfig;
