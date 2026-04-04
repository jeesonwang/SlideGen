import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const getPackageName = (id: string) => {
  const pathAfterNodeModules = id.split('node_modules/')[1]

  if (!pathAfterNodeModules) {
    return null
  }

  const parts = pathAfterNodeModules.split('/')

  if (parts[0].startsWith('@') && parts[1]) {
    return `${parts[0]}/${parts[1]}`
  }

  return parts[0]
}

// https://vite.dev/config/
export default defineConfig({
  cacheDir: '.vite',
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return undefined;
          }

          const packageName = getPackageName(id)

          if (!packageName) {
            return 'misc-vendor'
          }

          if (id.includes('/node_modules/antd/es/form') ||
              id.includes('/node_modules/antd/es/input') ||
              id.includes('/node_modules/antd/es/select') ||
              id.includes('/node_modules/antd/es/radio') ||
              id.includes('/node_modules/antd/es/switch') ||
              id.includes('/node_modules/antd/es/checkbox')) {
            return 'antd-form-vendor';
          }

          if (
            packageName === 'react' ||
            packageName === 'react-dom' ||
            packageName === 'scheduler' ||
            packageName === 'use-sync-external-store'
          ) {
            return 'react-vendor';
          }

          if (packageName === 'react-router' || packageName === 'react-router-dom') {
            return 'router-vendor';
          }

          if (
            packageName === 'markdown-it' ||
            packageName === 'react-markdown' ||
            packageName === 'react-markdown-editor-lite' ||
            packageName === 'remark-parse' ||
            packageName === 'remark-rehype' ||
            packageName === 'remark-stringify' ||
            packageName === 'rehype-raw' ||
            packageName === 'rehype-stringify' ||
            packageName === 'unified' ||
            packageName.startsWith('micromark') ||
            packageName.startsWith('mdast-') ||
            packageName.startsWith('hast-') ||
            packageName.startsWith('unist-') ||
            packageName === 'bail' ||
            packageName === 'trough' ||
            packageName === 'vfile'
          ) {
            return 'markdown-vendor';
          }

          if (
            packageName === '@tanstack/react-query' ||
            packageName === 'zustand'
          ) {
            return 'state-vendor';
          }

          if (
            packageName === 'react-hook-form' ||
            packageName === '@hookform/resolvers' ||
            packageName === 'zod'
          ) {
            return 'form-vendor';
          }

          if (
            packageName === 'axios' ||
            packageName === 'dayjs' ||
            packageName === 'clsx' ||
            packageName === 'tailwind-merge'
          ) {
            return 'utils-vendor';
          }

          return undefined;
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true,
      },
    },
  },
})
