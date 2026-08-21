import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/media': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
})
