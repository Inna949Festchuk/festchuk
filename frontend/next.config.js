// Server-side proxy target for /api/* rewrites.
// In Docker this must be the internal service name (http://backend:8000),
// NOT localhost (which inside the frontend container is the container itself).
// For local (non-Docker) dev, default to localhost.
const apiTarget = process.env.API_PROXY_TARGET || 'http://localhost:8000';

const withNextIntl = require('next-intl/plugin')('./i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Preserve trailing slashes so /api/* rewrites line up with DRF's
  // trailing-slash routes (avoids a Next 308 <-> Django 301 redirect loop).
  trailingSlash: true,
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/media/**',
      },
      {
        protocol: 'http',
        hostname: 'backend',
        port: '8000',
        pathname: '/media/**',
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
