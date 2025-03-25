/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // Export as static HTML
  distDir: 'out',
  images: {
    unoptimized: true, // Required for static export
  },
  trailingSlash: true, // For better compatibility with static file serving
  // Make Electron dev mode work with Next.js
  assetPrefix: process.env.NODE_ENV === 'production' ? './' : undefined,
  webpack: (config) => {
    return config;
  },
};

export default nextConfig;
