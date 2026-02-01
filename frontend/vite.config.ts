import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env from project root for shared configuration
  const rootEnv = loadEnv(mode, path.resolve(__dirname, '..'), '')

  return {
    plugins: [react()],
    define: {
      // Expose LOCALE as VITE_LOCALE for frontend code
      'import.meta.env.VITE_LOCALE': JSON.stringify(rootEnv.LOCALE || 'en'),
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
