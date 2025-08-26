/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: { appDir: true },
  reactStrictMode: true,
  typescript: {
    ignoreBuildErrors: true,
  },
};
module.exports = nextConfig;
