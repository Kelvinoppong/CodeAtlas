/** @type {import('next').NextConfig} */

const isStaticExport = process.env.STATIC_EXPORT === 'true';
const isGitHubPages = process.env.GITHUB_PAGES === 'true';

const nextConfig = {
  reactStrictMode: true,
  
  // Enable static export for GitHub Pages
  output: isStaticExport ? 'export' : undefined,
  
  // Base path for GitHub Pages (change 'CodeAtlas' to your repo name)
  basePath: isGitHubPages ? '/CodeAtlas' : '',
  assetPrefix: isGitHubPages ? '/CodeAtlas/' : '',
  
  // Disable image optimization for static export
  images: {
    unoptimized: isStaticExport,
  },
  
  // Skip type checking and linting during build (speeds up CI)
  eslint: {
    ignoreDuringBuilds: isStaticExport,
  },
  typescript: {
    ignoreBuildErrors: isStaticExport,
  },
  
  // Only enable server actions when not doing static export
  ...(isStaticExport ? {} : {
    experimental: {
      serverActions: {
        bodySizeLimit: "10mb",
      },
    },
  }),
  
  // Webpack config for handling problematic packages
  webpack: (config, { isServer }) => {
    // Fix for packages that don't work well with static export
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
