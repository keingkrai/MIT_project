import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Use /web/ base path for production builds (when served from FastAPI)
  // In development, use root path for Vite dev server
  base: command === 'build' ? '/web/' : '/',
  server: {
    port: 3000,
    open: true,
    // Proxy WebSocket connections to FastAPI backend during development
    proxy: {
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path, // Keep /ws as is
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
}))

