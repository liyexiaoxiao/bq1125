import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/control': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/logs': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/export': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/config': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/charts': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
