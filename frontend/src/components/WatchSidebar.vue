<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import {
  CalendarDays,
  CalendarRange,
  FileText,
  Tag,
} from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useSidebar } from '@/composables/useSidebar'

const { collapsed, mobileOpen, closeMobile } = useSidebar()
const route = useRoute()

// ── Nav items ────────────────────────────────────────────────────────────

interface NavItem {
  path: string
  name: string
  icon: any
  /** exact: require exact path match for active; false = prefix match */
  exact?: boolean
  /** datePrefix: also active for /watch/{YYYY-MM-DD} routes */
  datePrefix?: boolean
}

const navItems: NavItem[] = [
  { path: '/watch',          name: __('Today'),   icon: CalendarDays,  exact: true, datePrefix: true },
  { path: '/watch/week',     name: __('Week'),    icon: CalendarRange },
  { path: '/watch/prepare',  name: __('Prepare'), icon: FileText },
  { path: '/watch/tags',     name: __('Tags'),    icon: Tag },
]

// ── Active route detection ────────────────────────────────────────────────
// Today: exact /watch OR prefix /watch/YYYY-MM-DD (date routes)
// All others: prefix match

function isActive(item: NavItem): boolean {
  if (item.datePrefix) {
    return route.path === item.path ||
      /^\/watch\/\d{4}-\d{2}-\d{2}/.test(route.path)
  }
  if (item.exact) return route.path === item.path
  return route.path.startsWith(item.path)
}

// ── Item styling ─────────────────────────────────────────────────────────

function navItemClasses(item: NavItem): string {
  const active = isActive(item)
  return [
    'group sidebar-item flex items-center no-underline',
    'transition-all duration-200 rounded-r-lg relative min-h-[44px]',
    'focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-white/50 focus-visible:ring-offset-2',
    'focus-visible:ring-offset-watch-500',
    collapsed.value ? 'justify-center px-2 py-3 mx-1' : 'gap-3 px-4 py-3 mr-2',
    active
      ? 'bg-white/20 text-white font-semibold border-r-4 border-white'
      : 'text-white/90 hover:bg-white/10 hover:text-white',
  ].join(' ')
}

function iconClasses(item: NavItem): string {
  const active = isActive(item)
  return [
    'transition-transform duration-200 flex-shrink-0',
    collapsed.value ? 'w-6 h-6' : 'w-5 h-5',
    active ? 'scale-110' : 'group-hover:scale-105',
  ].join(' ')
}

// ── Version / links ───────────────────────────────────────────────────────

const VERSION    = '0.0.1'
const GITHUB_URL = 'https://github.com/Tonic-HQ/watch'
</script>

<template>
  <!-- Mobile backdrop -->
  <div
    v-if="mobileOpen"
    class="fixed inset-0 bg-black/50 z-30 sm:hidden"
    @click="closeMobile()"
  />

  <!-- Sidebar — single element, responsive via max-sm: variants -->
  <aside
    :class="[
      'flex-shrink-0 flex flex-col bg-watch-500 transition-all duration-200 h-full',
      collapsed ? 'w-16' : 'w-52',
      'max-sm:fixed max-sm:left-0 max-sm:top-14 max-sm:h-[calc(100vh-3.5rem)] max-sm:z-40 max-sm:w-52',
      mobileOpen ? 'max-sm:translate-x-0' : 'max-sm:-translate-x-full',
    ]"
    aria-label="Watch navigation"
  >
    <nav class="py-3 flex-1 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="navItemClasses(item)"
        :title="collapsed ? item.name : ''"
        @click="closeMobile()"
      >
        <component :is="item.icon" :class="iconClasses(item)" aria-hidden="true" />
        <span v-if="!collapsed" class="flex-1 text-sm">{{ item.name }}</span>
      </RouterLink>
    </nav>

    <div class="py-3 border-t border-watch-400">
      <div v-if="!collapsed" class="px-4 pb-2">
        <div class="text-sm font-semibold text-white/80">{{ __('Community Edition') }}</div>
        <div class="text-xs text-watch-200">v{{ VERSION }}</div>
      </div>
      <div :class="collapsed ? 'flex flex-col items-center gap-2 px-2' : 'flex items-center gap-4 px-4'">
        <a
          :href="GITHUB_URL"
          target="_blank"
          rel="noopener noreferrer"
          class="text-watch-200 hover:text-white transition-colors"
          :title="__('Source Code')"
          :aria-label="__('Source Code on GitHub (AGPL-3.0)')"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
        </a>
      </div>
    </div>
  </aside>
</template>
