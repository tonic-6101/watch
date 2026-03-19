/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors'
import dockPreset from '../../dock/frontend/src/styles/dock-tailwind-preset.js'

export default {
  presets: [dockPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        watch: colors.indigo,
        'watch-primary': '#6366f1',
        'watch-primary-light': '#eef2ff',
        'watch-primary-dark': '#4338ca',
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
