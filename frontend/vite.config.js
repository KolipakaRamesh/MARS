import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Alias to reach the root convex directory from anywhere in frontend
      '@convex': path.resolve(__dirname, '../convex'),
    },
  },
  server: {
    fs: {
      // Allow serving files from the root (where convex/ is)
      allow: [
        path.resolve(__dirname, '..')
      ]
    }
  }
})
