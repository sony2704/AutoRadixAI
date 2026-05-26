import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",          // required for Docker node server.js
  reactStrictMode: true,
  experimental: {
    serverComponentsExternalPackages: [],
  },
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "**",           // allow any local IP on the network
      },
    ],
  },
};

export default nextConfig;
