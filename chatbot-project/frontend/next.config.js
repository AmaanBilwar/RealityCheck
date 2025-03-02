module.exports = {
  reactStrictMode: true,
  env: {
    API_URL: process.env.API_URL || 'http://localhost:8000/api',
  },
  images: {
    domains: ['example.com'], // Add your image domains here
  },
}