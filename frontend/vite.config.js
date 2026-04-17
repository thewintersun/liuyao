import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [vue(), basicSsl()],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'https://localhost:9001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: '../static',
    emptyOutDir: true
  }
})
