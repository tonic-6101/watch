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

// ── Shared Vue runtime ──────────────────────────────────────────────
// Dock ships a single Vue ESM browser build. All ecosystem apps MUST use it
// so that cross-bundle components (DockNavbar) share one Vue instance.
const SHARED_VUE_URL = '/assets/dock/js/vendor/vue.esm.js'

function vueSharedPlugin(): Plugin {
  return {
    name: 'vue-shared',
    enforce: 'pre',
    resolveId(id) {
      if (id === 'vue' || id === '@vue/runtime-dom' || id === '@vue/runtime-core' || id === '@vue/reactivity') {
        return { id: SHARED_VUE_URL, external: true }
      }
    },
  }
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
    <link rel="stylesheet" href="/assets/dock/css/dock-tokens.css">
    <link rel="stylesheet" href="/assets/dock/css/dock-navbar.css">
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

// ── Settings ESM build ──────────────────────────────────────────────
// Builds watch-settings.esm.js — a standalone ESM bundle that exports
// WatchSettings component for Dock's unified settings hub.
// This runs as a secondary build after the main SPA build.
function settingsEsmPlugin(): Plugin {
  return {
    name: 'watch-settings-esm',
    async closeBundle() {
      const { build } = await import('vite')
      await build({
        configFile: false,
        base: '/assets/watch/js/',
        plugins: [
          vueSharedPlugin(),
          vue(),
          // Include frappe-ui plugin so ~icons and frappe-ui components resolve
          ...(frappeui ? [frappeui({ frappeProxy: false, lucideIcons: true, jinjaBootData: false })] : []),
        ],
        resolve: {
          alias: {
            '@': path.resolve(__dirname, 'src'),
          },
        },
        build: {
          outDir: path.resolve(__dirname, '../watch/public/js'),
          emptyOutDir: false,
          lib: {
            entry: path.resolve(__dirname, 'src/dock-settings.ts'),
            formats: ['es'],
            fileName: () => 'watch-settings.esm.js',
          },
          rollupOptions: {
            external: [
              'vue',
              '@vue/runtime-dom',
              '@vue/runtime-core',
              '@vue/reactivity',
              /^\/assets\/dock\//,
            ],
            output: {
              paths: {
                vue: '/assets/dock/js/vendor/vue.esm.js',
              },
            },
          },
        },
      })
      console.log('Built watch-settings.esm.js')
    },
  }
}

export default defineConfig({
  base: '/assets/watch/frontend/',
  plugins: [
    vueSharedPlugin(),
    vue(),
    frappeui && frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
    }),
    frappeManifestPlugin(),
    settingsEsmPlugin(),
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
    include: ['frappe-ui', 'feather-icons', 'lucide-vue-next', 'vue-router'],
  },
})
