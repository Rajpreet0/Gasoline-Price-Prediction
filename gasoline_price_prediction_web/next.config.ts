import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [{ hostname: "www.google.com" }]
  }
};

export default nextConfig;
