import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/media': backendTarget,
      '/static': backendTarget,
    },
  },
  preview: {
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/media': backendTarget,
      '/static': backendTarget,
    },
  },
  build: {
    outDir: 'dist',
  },
})
