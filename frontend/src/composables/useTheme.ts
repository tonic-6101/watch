// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, onMounted } from 'vue'

// Standalone key — spec: '{app}-theme' for app-owned theme (account-menu.md)
const THEME_KEY = 'watch-theme'

export function useTheme() {
  const theme = ref<'light' | 'dark' | 'system'>(
    (localStorage.getItem(THEME_KEY) as 'light' | 'dark' | 'system') ?? 'system'
  )

  function apply(t: typeof theme.value) {
    const dark =
      t === 'dark' ||
      (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', dark)
  }

  function setTheme(t: typeof theme.value) {
    theme.value = t
    localStorage.setItem(THEME_KEY, t)
    apply(t)
  }

  onMounted(() => apply(theme.value))

  return { theme, setTheme }
}
