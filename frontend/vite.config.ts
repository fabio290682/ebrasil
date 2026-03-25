import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: (() => {
    if (process.env.GITHUB_PAGES === 'true') {
      const repo = (process.env.GITHUB_REPOSITORY || '').split('/')[1]
      if (repo) return `/${repo}/`
    }
    return '/'
  })(),
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
