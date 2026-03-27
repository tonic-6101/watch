<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
// @ts-ignore — served by Dock's built assets
import { DockLayout, DockSidebarShell } from '/assets/dock/js/dock-navbar.esm.js'
import { CalendarDays, CalendarRange, CalendarSearch, FileText, Tag } from 'lucide-vue-next'
import PreferencesPanel from './components/PreferencesPanel.vue'
import ShortcutsOverlay from './components/ShortcutsOverlay.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useTimer } from './composables/useTimer'
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts'
import { __ } from '@/composables/useTranslate'

declare const __APP_VERSION__: string

const watchNavItems = [
  { key: 'today',   label: __('Today'),   icon: CalendarDays,   path: '/watch',          exact: true },
  { key: 'week',    label: __('Week'),     icon: CalendarRange,  path: '/watch/week' },
  { key: 'range',   label: __('Range'),    icon: CalendarSearch, path: '/watch/range' },
  { key: 'prepare', label: __('Prepare'),  icon: FileText,       path: '/watch/prepare' },
  { key: 'tags',    label: __('Tags'),     icon: Tag,            path: '/watch/tags' },
]

const watchFooter = {
  edition: __('Community Edition'),
  version: __APP_VERSION__,
  sourceUrl: 'https://github.com/Tonic-HQ/watch',
}

// ── Timer (singleton state — safe to call here) ──────────────────────────

const timer = useTimer()

// ── Router ───────────────────────────────────────────────────────────────

const router = useRouter()
const route  = useRoute()

// ── Preferences panel (slide-over) ──────────────────────────────────────

const showPreferences = ref(false)

function openPreferences() { showPreferences.value = true }
function closePreferences() {
  showPreferences.value = false
  // Remove ?panel=preferences from URL without navigation
  if (route.query.panel === 'preferences') {
    const query = { ...route.query }
    delete query.panel
    router.replace({ ...route, query })
  }
}

// Open on ?panel=preferences query param
watch(() => route.query.panel, (val) => {
  if (val === 'preferences') showPreferences.value = true
}, { immediate: true })

// Expose openPreferences globally so external components can trigger it
;(window as any).__watchOpenPreferences = openPreferences

// ── Help overlay ─────────────────────────────────────────────────────────

const showHelp = ref(false)

function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

// ── Shortcut handlers ────────────────────────────────────────────────────

async function onTimerToggle() {
  try {
    if (timer.state.value === 'stopped') {
      await timer.start('', [], 'billable')
    } else if (timer.state.value === 'running') {
      await timer.pause()
    } else {
      await timer.resume()
    }
  } catch { /* silent — Dock timer panel shows errors */ }
}

async function onTimerStop() {
  if (timer.state.value === 'stopped') return
  try {
    await timer.stop('')
  } catch { /* silent — Dock timer panel shows errors */ }
}

function onNewEntry() {
  const isDaily = route.path === '/watch' || /^\/watch\/\d{4}-\d{2}-\d{2}$/.test(route.path)
  if (isDaily) {
    window.dispatchEvent(new CustomEvent('watch:focus-entry-bar'))
  } else {
    router.push('/watch').then(() => {
      window.dispatchEvent(new CustomEvent('watch:focus-entry-bar'))
    })
  }
}

function onGoToday() {
  router.push('/watch')
}

function onGoWeek() {
  router.push('/watch/week')
}

function onGoPrepare() {
  router.push('/watch/prepare')
}

function onHelp() {
  showHelp.value = !showHelp.value
}

function onEsc() {
  showHelp.value = false
}

useKeyboardShortcuts({
  onTimerToggle,
  onTimerStop,
  onNewEntry,
  onGoToday,
  onGoWeek,
  onGoPrepare,
  onHelp,
  onEsc,
})
</script>

<template>
  <ToastContainer />

  <DockLayout>
    <DockSidebarShell
      color="#6366f1"
      :items="watchNavItems"
      :footer="watchFooter"
      aria-label="Watch navigation"
    />
    <main class="flex-1 overflow-y-auto">
      <RouterView />
    </main>
  </DockLayout>

  <!-- My Preferences slide-over -->
  <PreferencesPanel v-if="showPreferences" @close="closePreferences" />

  <!-- Keyboard shortcuts overlay (H key) -->
  <ShortcutsOverlay v-if="showHelp" @close="showHelp = false" />
</template>
