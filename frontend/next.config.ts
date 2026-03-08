import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /api/v1/* to FastAPI backend during development.
  // In production (Docker), the browser talks to the backend directly
  // via NEXT_PUBLIC_API_URL.
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
