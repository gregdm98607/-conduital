import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: parseInt(env.VITE_PORT || '5173'),
      proxy: {
        '/api': {
          target: env.VITE_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/modules': {
          target: env.VITE_API_TARGET || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
