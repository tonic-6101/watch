<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { User, SlidersHorizontal, Settings, LogOut } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useTheme } from '@/composables/useTheme'

// ── Props / emits ─────────────────────────────────────────────────────────

const props = defineProps<{ open: boolean }>()
const emit  = defineEmits<{ toggle: [] }>()

// ── Dock detection ────────────────────────────────────────────────────────

const dockInstalled = computed(() =>
  !!(window as any).frappe?.boot?.dock?.installed
)

// ── User identity ─────────────────────────────────────────────────────────

const frappe       = (window as any).frappe
const sessionUser  = frappe?.session?.user ?? 'Guest'
const userFullName = frappe?.boot?.user?.full_name ?? sessionUser
const userEmail    = frappe?.boot?.user?.email ?? ''
const userImage    = frappe?.boot?.user?.user_image ?? null
const userInitial  = computed(() =>
  (userFullName as string).charAt(0).toUpperCase()
)

// ── Theme ─────────────────────────────────────────────────────────────────

const { theme, setTheme } = useTheme()

function openPreferences() {
  ;(window as any).__watchOpenPreferences?.()
}

const themeOptions = [
  { value: 'system' as const, label: __('System') },
  { value: 'light'  as const, label: __('Light')  },
  { value: 'dark'   as const, label: __('Dark')   },
]
</script>

<template>
  <!-- Trigger: avatar button -->
  <button
    class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0
           bg-watch-500 hover:opacity-90 transition-opacity
           flex items-center justify-center
           text-white text-xs font-semibold"
    :aria-expanded="open"
    aria-haspopup="true"
    :aria-label="__('Account menu')"
    :title="userFullName"
    @click="emit('toggle')"
  >
    <img
      v-if="userImage"
      :src="userImage"
      :alt="userFullName"
      class="w-full h-full object-cover"
    />
    <span v-else aria-hidden="true">{{ userInitial }}</span>
  </button>

  <!-- Dropdown panel -->
  <Transition
    enter-active-class="transition ease-out duration-150"
    enter-from-class="opacity-0 translate-y-1.5"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition ease-in duration-100"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 translate-y-1.5"
  >
    <div
      v-if="open"
      role="menu"
      class="absolute right-0 top-full mt-2 w-56 rounded-lg shadow-lg z-20
             border border-[var(--dock-border)] bg-white dark:bg-[#1a1f2e] overflow-hidden"
    >
      <!-- Section 1 — Identity header (non-interactive) -->
      <div class="px-3 py-2.5 border-b border-[var(--dock-border)]">
        <p class="text-sm font-medium text-[var(--dock-text)] truncate">{{ userFullName }}</p>
        <p class="text-xs text-[var(--dock-icon)] truncate mt-0.5">{{ userEmail }}</p>
      </div>

      <!-- Section 2 — Core nav items -->
      <div class="py-1 border-b border-[var(--dock-border)]">
        <a
          :href="`/app/user/${encodeURIComponent(sessionUser)}`"
          role="menuitem"
          class="flex items-center gap-2 px-3 py-1.5 text-sm text-[var(--dock-text)] no-underline
                 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          @click="emit('toggle')"
        >
          <User class="w-4 h-4 text-[var(--dock-icon)]" aria-hidden="true" />
          {{ __('My Profile') }}
        </a>
        <button
          role="menuitem"
          class="flex items-center gap-2 px-3 py-1.5 text-sm text-[var(--dock-text)] w-full text-left
                 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          @click="emit('toggle'); openPreferences()"
        >
          <SlidersHorizontal class="w-4 h-4 text-[var(--dock-icon)]" aria-hidden="true" />
          {{ __('My Preferences') }}
        </button>
      </div>

      <!-- Section 3 — Soft-dependency items (omitted entirely when empty) -->
      <!-- In standalone watch, no other apps are available from here -->

      <!-- Section 4 — Theme toggle (hidden when Dock manages theming) -->
      <div
        v-if="!dockInstalled"
        class="px-4 py-3 border-b border-[var(--dock-border)]"
        @click.stop
      >
        <!-- Section label -->
        <div class="flex items-center gap-2 mb-2">
          <Settings class="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" aria-hidden="true" />
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {{ __('Theme') }}
          </span>
        </div>

        <!-- 3-segment text toggle -->
        <div
          class="flex gap-1 bg-gray-100 dark:bg-gray-900 rounded-lg p-1"
          role="radiogroup"
          :aria-label="__('Theme preference')"
        >
          <button
            v-for="opt in themeOptions"
            :key="opt.value"
            class="flex-1 px-3 py-1.5 text-xs font-medium rounded transition-colors"
            :class="theme === opt.value
              ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'"
            role="radio"
            :aria-checked="theme === opt.value"
            @click="setTheme(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Section 5 — Log out -->
      <div class="py-1">
        <a
          href="/app/logout"
          role="menuitem"
          class="flex items-center gap-2 px-3 py-1.5 text-sm no-underline
                 text-red-600 dark:text-red-400
                 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        >
          <LogOut class="w-4 h-4" aria-hidden="true" />
          {{ __('Log out') }}
        </a>
      </div>
    </div>
  </Transition>
</template>
