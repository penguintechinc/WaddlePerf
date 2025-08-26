/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
  reactStrictMode: true,
  // swcMinify is deprecated in Next.js 15+, removing it
  distDir: 'out'
}

module.exports = nextConfig