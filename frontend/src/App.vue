<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, defineAsyncComponent } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import WatchSidebar from './components/WatchSidebar.vue'
import PreferencesPanel from './components/PreferencesPanel.vue'
import ShortcutsOverlay from './components/ShortcutsOverlay.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useTimer } from './composables/useTimer'
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts'

const dockInstalled = computed(() =>
  !!(window as any).frappe?.boot?.dock?.installed
)

const NavbarComponent = dockInstalled.value
  ? defineAsyncComponent(() =>
      // @ts-ignore — runtime URL, only resolves when Dock is installed
      import('/assets/dock/js/dock-navbar.esm.js').then((m: any) => m.DockNavbar)
    )
  : defineAsyncComponent(() => import('./components/WatchNavbar.vue'))

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

// Expose openPreferences globally so WatchAccountMenu can call it
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
  } catch { /* errors shown in TimerWidget */ }
}

async function onTimerStop() {
  if (timer.state.value === 'stopped') return
  try {
    await timer.stop('')
  } catch { /* errors shown in TimerWidget */ }
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
  <div class="flex flex-col h-screen overflow-hidden">
    <!-- Top bar -->
    <component :is="NavbarComponent" />

    <!-- Body: sidebar + page content -->
    <div class="flex flex-1 overflow-hidden">
      <WatchSidebar />
      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
    </div>

    <!-- My Preferences slide-over -->
    <PreferencesPanel v-if="showPreferences" @close="closePreferences" />

    <!-- Keyboard shortcuts overlay (H key) -->
    <ShortcutsOverlay v-if="showHelp" @close="showHelp = false" />

    <!-- Toast notifications -->
    <ToastContainer />
  </div>
</template>
