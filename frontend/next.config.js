/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const appBase = process.env.APP_URL || "http://127.0.0.1:8000";
    return [
      {
        source: "/api/py/:path*",
        destination: `${appBase}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
