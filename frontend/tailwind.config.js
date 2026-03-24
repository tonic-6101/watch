import dockPreset from '../../dock/frontend/src/styles/dock-tailwind-preset.js'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [dockPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
    // Dock shared pages loaded at runtime via ESM — scan source so
    // Tailwind generates the utility classes they use (calendar, people, etc.)
    '../../dock/frontend/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Domain-specific colors (not part of shared design system)
        'entry-billable': '#6366f1',
        'entry-nonbillable': '#6b7280',
        'entry-internal': '#f59e0b',
        'timer-running': '#10b981',
        'timer-paused': '#f59e0b',
        'timer-stopped': '#6b7280',
      },
    },
  },
  plugins: [],
}
