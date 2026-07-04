import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: __dirname,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  webpack: (config) => {
    config.resolve.alias["react-router-dom"] = path.resolve(
      __dirname,
      "src/lib/router-compat.js",
    );
    return config;
  },
};

export default nextConfig;
