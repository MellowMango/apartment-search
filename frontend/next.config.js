/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Prefer TypeScript pages in src/pages, but allow JavaScript as fallback
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
  // Use src directory to correctly detect pages
  experimental: {
    appDir: false,  // Keep using pages directory
  },
  images: {
    domains: ['images.unsplash.com'],
  },
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_MAPBOX_TOKEN: process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.eyJ1IjoiYWNxdWlyZWFwYXJ0bWVudHMiLCJhIjoiY204NTRvMjZ5MGx1dDJrb2t0MXo5c2QxNSJ9.-B71BMKr2rwUBCvvqDRbmg',
  },
  basePath: '',
  trailingSlash: false,
  // Custom webpack config to conditionally handle TS/JS files
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Add any custom webpack rules here if needed for the migration
    return config;
  },
}

module.exports = nextConfig 