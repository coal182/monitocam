import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8585',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/api/, '')
      },
      '/auth': {
        target: 'http://localhost:8585',
        changeOrigin: true
      },
      '/cameras': {
        target: 'http://localhost:8585',
        changeOrigin: true
      }
    }
  }
})
