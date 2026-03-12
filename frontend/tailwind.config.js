/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors'

export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Watch brand — full indigo scale (watch-50 … watch-950)
        watch: colors.indigo,

        // Semantic aliases used in components
        'watch-primary': '#6366f1',
        'watch-primary-light': '#eef2ff',
        'watch-primary-dark': '#4338ca',

        // Entry type colours
        'entry-billable': '#6366f1',
        'entry-nonbillable': '#6b7280',
        'entry-internal': '#f59e0b',

        // Timer states
        'timer-running': '#10b981',
        'timer-paused': '#f59e0b',
        'timer-stopped': '#6b7280',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
