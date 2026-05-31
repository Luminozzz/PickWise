import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During dev, requests to /api/* are proxied to the FastAPI backend so the
// browser talks to a single origin (no CORS dance, even though the backend
// already allows all origins). Override the target with VITE_API_TARGET.
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
})