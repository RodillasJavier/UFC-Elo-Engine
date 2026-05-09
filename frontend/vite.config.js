/**
 * frontend/vite.config.js
 * 
 * Vite configuration file for the frontend React application. This file sets up the development server and configures a proxy to forward API requests to the backend server running on localhost:8000.
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
