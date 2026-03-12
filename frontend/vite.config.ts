// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

// Type for frappe-ui vite plugin
type FrappeUIVitePlugin = (options?: {
  frappeProxy?: boolean
  lucideIcons?: boolean
  jinjaBootData?: boolean
}) => Plugin

// Try to load frappe-ui vite plugin
let frappeui: FrappeUIVitePlugin | undefined
try {
  const module = await import('frappe-ui/vite')
  frappeui = module.default as FrappeUIVitePlugin
} catch {
  console.warn('frappe-ui vite plugin not found, continuing without it')
}

interface BundleChunk {
  type: 'asset' | 'chunk'
  fileName: string
  isEntry?: boolean
}

interface FrappeManifest {
  js?: string
  css?: string
}

function frappeManifestPlugin(): Plugin {
  return {
    name: 'frappe-manifest',
    writeBundle(options, bundle: Record<string, BundleChunk>): void {
      const manifest: FrappeManifest = {}
      const cssFiles: string[] = []

      for (const [fileName, chunk] of Object.entries(bundle)) {
        if (chunk.type === 'asset' || chunk.type === 'chunk') {
          if (fileName.endsWith('.js') && chunk.isEntry) {
            manifest.js = fileName
          }
          if (fileName.endsWith('.css')) {
            cssFiles.push(fileName)
          }
        }
      }
      manifest.css = cssFiles.find(f => f.includes('main-')) || cssFiles[0]

      const manifestPath = path.resolve(options.dir || '', 'manifest.json')
      fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2))

      const jsFile = manifest.js?.replace('assets/', '') || ''
      const cssFile = manifest.css?.replace('assets/', '') || ''

      const htmlContent = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Watch</title>
    <meta name="description" content="Watch — Time tracking for Frappe" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
    <link rel="icon" type="image/svg+xml" href="/assets/watch/images/logo.svg" />
    <script type="module" crossorigin src="/assets/watch/frontend/assets/${jsFile}"></script>
    <link rel="stylesheet" crossorigin href="/assets/watch/frontend/assets/${cssFile}">
  </head>
  <body>
    <script>
      (function() {
        var stored = localStorage.getItem('dock-theme');
        var isDark = stored === 'dark' ||
          (!stored || stored === 'auto') && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDark) document.documentElement.classList.add('dark');
      })();
    </script>
    <div id="app" class="h-screen"></div>
    <div id="modals"></div>
    <div id="popovers"></div>
    <script>
      window.csrf_token = "{{ csrf_token }}"
    </script>
    {% for key in boot %}
    <script>
      window["{{ key }}"] = {{ boot[key] | tojson }};
    </script>
    {% endfor %}
  </body>
</html>`

      const htmlPath = path.resolve(__dirname, '../watch/www/watch.html')
      fs.writeFileSync(htmlPath, htmlContent)
      console.log('Generated watch.html with assets:', manifest)
    }
  }
}

export default defineConfig({
  base: '/assets/watch/frontend/',
  plugins: [
    vue(),
    frappeui && frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
    }),
    frappeManifestPlugin(),
  ].filter(Boolean) as Plugin[],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../watch/public/frontend',
    emptyOutDir: true,
    target: 'es2015',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      // Dock ESM bundle is a runtime browser URL — never resolved at build time
      external: ['/assets/dock/js/dock-navbar.esm.js'],
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '^/(api|assets|files)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    include: ['frappe-ui', 'feather-icons', 'lucide-vue-next', 'vue', 'vue-router'],
  },
})
