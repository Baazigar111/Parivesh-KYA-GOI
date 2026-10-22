import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  env: {
    API_URL: process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "",
  },
};

export default nextConfig;
