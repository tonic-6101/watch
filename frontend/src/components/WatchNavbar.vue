<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { Menu, Search, Bell, Grid3X3, Play, Pause, Clock, Tag } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useSidebar } from '@/composables/useSidebar'
import { useTimer, formatElapsed } from '@/composables/useTimer'
import { useSearch } from '@/composables/useSearch'
import WatchAccountMenu from './WatchAccountMenu.vue'
import TimerWidget from './timer/TimerWidget.vue'

// ── Watch-specific constants ────────────────────────────────────────────
const APP_NAME  = 'Watch'
const APP_ICON  = '/assets/watch/images/logo.svg'
const APP_COLOR = '#6366f1'
const APP_ROUTE = '/watch'
const SEARCH_SECTIONS = [
  { label: 'Time Entries', value: 'time-entries' },
  { label: 'Tags',         value: 'tags'         },
]

const ICON_MAP: Record<string, any> = {
  clock: Clock,
  tag: Tag,
  play: Play,
}
// ───────────────────────────────────────────────────────────────────────

const sidebar = useSidebar()
const timer = useTimer()
const search = useSearch()

const scrolled     = ref(false)
const timerOpen    = ref(false)
const bellOpen     = ref(false)
const switcherOpen = ref(false)
const menuOpen     = ref(false)
const searchInput  = ref<HTMLInputElement | null>(null)
const searchContainer = ref<HTMLElement | null>(null)

const unreadCount  = ref(0)

function getIcon(iconName: string) {
  return ICON_MAP[iconName] ?? Search
}

// Compute flat index for keyboard navigation across grouped sections
function flatIndex(sectionIndex: number, resultIndex: number): number {
  let idx = 0
  for (let s = 0; s < sectionIndex; s++) {
    idx += search.sections.value[s].results.length
  }
  return idx + resultIndex
}

// Close search dropdown on outside click
function handleSearchOutsideClick(e: MouseEvent) {
  if (searchContainer.value && !searchContainer.value.contains(e.target as Node)) {
    search.close()
  }
}

function closeAll() {
  timerOpen.value    = false
  bellOpen.value     = false
  switcherOpen.value = false
  menuOpen.value     = false
}

// Opening one dropdown closes all others
function toggleDropdown(which: 'timer' | 'bell' | 'switcher' | 'menu') {
  const refs = { timer: timerOpen, bell: bellOpen, switcher: switcherOpen, menu: menuOpen }
  const next = !refs[which].value
  closeAll()
  refs[which].value = next
}

// Close when clicking outside all dropdowns
function handleOutsideClick(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest('[data-dropdown]')) closeAll()
}

// Escape key closes any open dropdown
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeAll()
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    if (window.innerWidth >= 768) searchInput.value?.focus()
  }
}

onMounted(() => {
  document.documentElement.style.setProperty('--dock-accent', APP_COLOR)

  window.addEventListener('scroll', () => {
    scrolled.value = window.scrollY > 4
  }, { passive: true })

  document.addEventListener('click', handleOutsideClick)
  document.addEventListener('click', handleSearchOutsideClick)
  document.addEventListener('keydown', handleKeydown)
})
</script>

<template>
  <header
    role="banner"
    :class="[
      'h-14 sticky top-0 z-50 flex items-center gap-2 px-4 select-none',
      'bg-[var(--dock-bg)] text-[var(--dock-text)] transition-shadow duration-150',
      scrolled
        ? 'shadow-sm'
        : 'border-b border-[var(--dock-border)] border-opacity-50',
    ]"
  >
    <!-- 1. Sidebar toggle -->
    <button
      class="flex items-center justify-center w-8 h-8 rounded-md flex-shrink-0
             text-[var(--dock-icon)] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
      :aria-label="__('Toggle sidebar')"
      :title="__('Toggle sidebar')"
      @click="sidebar.toggle()"
    >
      <Menu class="w-5 h-5" aria-hidden="true" />
    </button>

    <!-- 2. App label -->
    <a
      :href="APP_ROUTE"
      class="flex items-center gap-2 min-w-0 flex-shrink-0 no-underline"
    >
      <img :src="APP_ICON" :alt="APP_NAME" class="w-6 h-6 rounded-md flex-shrink-0" />
      <span class="text-sm font-medium text-[var(--dock-text)] truncate max-w-[140px]">
        {{ APP_NAME }}
      </span>
    </a>

    <!-- 3. Search — center fill -->
    <div class="flex-1 flex justify-center px-4">
      <!-- Desktop inline bar -->
      <div ref="searchContainer" class="hidden md:flex items-center flex-1 max-w-lg mx-4 relative">
        <div
          class="flex items-center w-full h-9 rounded-lg border border-[var(--dock-border)]
                 bg-[var(--dock-bg)] overflow-hidden transition-all
                 focus-within:ring-2 focus-within:ring-[var(--dock-accent)]/30
                 focus-within:border-[var(--dock-accent)]"
        >
          <select
            v-model="search.scope.value"
            class="h-full px-3 text-sm text-[var(--dock-icon)]
                   bg-black/5 dark:bg-white/5 border-r border-[var(--dock-border)]
                   outline-none cursor-pointer shrink-0"
          >
            <option value="">{{ __('All') }}</option>
            <option
              v-for="section in SEARCH_SECTIONS"
              :key="section.value"
              :value="section.value"
            >
              {{ __(section.label) }}
            </option>
          </select>
          <input
            ref="searchInput"
            v-model="search.query.value"
            type="text"
            :placeholder="__('Search...')"
            class="flex-1 h-full px-3 text-sm bg-transparent
                   text-[var(--dock-text)] placeholder-[var(--dock-icon)]
                   outline-none min-w-0"
            @keydown="search.handleKeydown($event)"
            @focus="search.query.value.trim() && (search.open.value = true)"
          />
          <button
            class="h-full px-3 text-[var(--dock-icon)] hover:text-[var(--dock-text)] transition-colors"
            :aria-label="__('Search')"
          >
            <Search class="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <!-- Search suggestions dropdown -->
        <div
          v-if="search.open.value && search.sections.value.length > 0"
          class="absolute left-0 right-0 top-full mt-1 z-30 bg-[var(--dock-bg)]
                 border border-[var(--dock-border)] rounded-xl shadow-lg
                 max-h-[400px] overflow-y-auto"
        >
          <template v-for="(section, si) in search.sections.value" :key="section.title">
            <div class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--dock-icon)]">
              {{ __(section.title) }}
            </div>
            <button
              v-for="(result, ri) in section.results"
              :key="ri"
              type="button"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2 text-left transition-colors',
                search.activeIndex.value === flatIndex(si, ri)
                  ? 'bg-[var(--dock-accent)]/10'
                  : 'hover:bg-black/5 dark:hover:bg-white/5',
              ]"
              @click="search.selectResult(result)"
              @mouseenter="search.activeIndex.value = flatIndex(si, ri)"
            >
              <component
                :is="getIcon(result.icon)"
                class="w-4 h-4 shrink-0 text-[var(--dock-icon)]"
                aria-hidden="true"
              />
              <div class="flex-1 min-w-0">
                <div class="text-sm text-[var(--dock-text)] truncate">{{ result.label }}</div>
                <div v-if="result.description" class="text-xs text-[var(--dock-icon)] truncate">
                  {{ result.description }}
                </div>
              </div>
            </button>
          </template>
        </div>

        <!-- Loading indicator -->
        <div
          v-else-if="search.open.value && search.loading.value"
          class="absolute left-0 right-0 top-full mt-1 z-30 bg-[var(--dock-bg)]
                 border border-[var(--dock-border)] rounded-xl shadow-lg px-3 py-3
                 text-sm text-[var(--dock-icon)]"
        >
          {{ __('Searching…') }}
        </div>

        <!-- No results -->
        <div
          v-else-if="search.open.value && !search.loading.value && search.query.value.trim().length >= 2"
          class="absolute left-0 right-0 top-full mt-1 z-30 bg-[var(--dock-bg)]
                 border border-[var(--dock-border)] rounded-xl shadow-lg px-3 py-3
                 text-sm text-[var(--dock-icon)]"
        >
          {{ __('No results for "{0}"', [search.query.value]) }}
        </div>
      </div>

      <!-- Mobile icon button -->
      <button
        class="md:hidden flex items-center justify-center w-8 h-8 rounded-md flex-shrink-0
               text-[var(--dock-icon)] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        :aria-label="__('Search')"
        :title="__('Search')"
      >
        <Search class="w-4 h-4" aria-hidden="true" />
      </button>
    </div>

    <!-- Right slot cluster -->
    <div class="flex items-center gap-1 flex-shrink-0">

      <!-- 4. Timer popover -->
      <div class="relative" data-dropdown>
        <button
          class="flex items-center gap-1.5 h-8 rounded-md flex-shrink-0 px-1.5
                 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          :aria-expanded="timerOpen"
          aria-haspopup="true"
          :aria-label="__('Timer')"
          :title="__('Timer')"
          @click="toggleDropdown('timer')"
        >
          <!-- Stopped: play icon -->
          <Play
            v-if="timer.isStopped.value"
            class="w-4 h-4 text-[var(--dock-icon)]"
            fill="currentColor"
            aria-hidden="true"
          />
          <!-- Running: pulsing dot + elapsed -->
          <template v-else-if="timer.isRunning.value">
            <span
              class="inline-block w-2 h-2 rounded-full bg-[var(--dock-accent)] animate-pulse flex-shrink-0"
              aria-hidden="true"
            />
            <span class="text-xs font-mono tabular-nums text-[var(--dock-accent)] leading-none select-none">
              {{ formatElapsed(timer.elapsed.value) }}
            </span>
          </template>
          <!-- Paused: static dot + elapsed (dimmed) -->
          <template v-else>
            <Pause
              class="w-3.5 h-3.5 text-[var(--dock-icon)] opacity-70"
              fill="currentColor"
              aria-hidden="true"
            />
            <span class="text-xs font-mono tabular-nums text-[var(--dock-icon)] opacity-70 leading-none select-none">
              {{ formatElapsed(timer.elapsed.value) }}
            </span>
          </template>
        </button>

        <Transition
          enter-active-class="transition ease-out duration-150"
          enter-from-class="opacity-0 translate-y-1.5"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-100"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-1.5"
        >
          <div
            v-show="timerOpen"
            class="absolute right-0 mt-2 rounded-xl shadow-lg z-20
                   border border-[var(--dock-border)] bg-white dark:bg-[#1a1f2e]"
            style="width: 340px; top: 100%"
            @click.stop
          >
            <TimerWidget @stopped="timerOpen = false" />
          </div>
        </Transition>
      </div>

      <!-- 5. Bell -->
      <div class="relative" data-dropdown>
        <button
          class="flex items-center justify-center w-8 h-8 rounded-md flex-shrink-0
                 text-[var(--dock-icon)] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          :aria-expanded="bellOpen"
          :aria-label="__('Notifications')"
          :title="__('Notifications')"
          @click="toggleDropdown('bell')"
        >
          <Bell class="w-4 h-4" aria-hidden="true" />
          <span
            v-if="unreadCount > 0"
            class="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1
                   bg-red-500 text-white text-[10px] font-bold leading-none
                   rounded-full flex items-center justify-center"
            :aria-label="`${unreadCount} ${__('unread notifications')}`"
          >
            {{ unreadCount > 99 ? '99+' : unreadCount }}
          </span>
        </button>

        <Transition
          enter-active-class="transition ease-out duration-150"
          enter-from-class="opacity-0 translate-y-1.5"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-100"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-1.5"
        >
          <div
            v-if="bellOpen"
            class="absolute right-0 mt-2 rounded-lg shadow-lg z-20
                   border border-[var(--dock-border)] bg-white dark:bg-[#1a1f2e]"
            style="width: 320px; top: 100%"
          >
            <div class="px-3 py-2.5 text-sm text-[var(--dock-icon)]">
              {{ __('No notifications') }}
            </div>
          </div>
        </Transition>
      </div>

      <!-- 8. App switcher -->
      <div class="relative" data-dropdown>
        <button
          class="flex items-center justify-center w-8 h-8 rounded-md flex-shrink-0
                 text-[var(--dock-icon)] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          :aria-expanded="switcherOpen"
          aria-haspopup="true"
          :aria-label="__('Open app switcher')"
          :title="__('App switcher')"
          @click="toggleDropdown('switcher')"
        >
          <Grid3X3 class="w-4 h-4" aria-hidden="true" />
        </button>

        <Transition
          enter-active-class="transition ease-out duration-150"
          enter-from-class="opacity-0 translate-y-1.5"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-100"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-1.5"
        >
          <div
            v-if="switcherOpen"
            class="absolute right-0 mt-2 rounded-lg shadow-lg z-20
                   border border-[var(--dock-border)] bg-white dark:bg-[#1a1f2e] p-3"
            style="width: 224px; top: 100%"
          >
            <a
              :href="APP_ROUTE"
              class="flex items-center gap-3 p-2 rounded-md hover:bg-black/5
                     dark:hover:bg-white/5 no-underline transition-colors"
            >
              <img :src="APP_ICON" :alt="APP_NAME" class="w-7 h-7 rounded-md flex-shrink-0" />
              <span class="text-sm font-medium text-[var(--dock-text)]">{{ APP_NAME }}</span>
            </a>
          </div>
        </Transition>
      </div>

      <!-- 9. Account menu -->
      <div class="relative" data-dropdown>
        <WatchAccountMenu
          :open="menuOpen"
          @toggle="toggleDropdown('menu')"
        />
      </div>

    </div>
  </header>
</template>
