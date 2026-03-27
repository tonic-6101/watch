<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Custom date range report — arbitrary from/to date range summary.
-->
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { CalendarRange, ChevronDown, ChevronRight } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { formatHours } from '@/composables/useEntries'

// ── Types ──────────────────────────────────────────────────────

interface TagMeta {
  tag_name: string | null
  color: string | null
  hours: number
  pct: number
}

interface DaySummary {
  date: string
  total_hours: number
  billable_hours: number
  rounded_total_hours: number
  rounded_billable_hours: number
  entry_count: number
  top_tags: { tag_name: string; color: string | null; category: string | null }[]
  overflow_count: number
  is_work_day: boolean
}

interface RangeSummary {
  from_date: string
  to_date: string
  days: DaySummary[]
  tags: TagMeta[]
  total_hours: number
  billable_hours: number
  rounded_total_hours: number
  rounded_billable_hours: number
}

// ── State ──────────────────────────────────────────────────────

const loading = ref(false)
const error = ref('')
const data = ref<RangeSummary | null>(null)

// Date range — default to current month
const today = new Date()
const fromDate = ref(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`)
const toDate = ref(today.toISOString().slice(0, 10))

// Preset support
const preset = ref('this_month')
const PRESETS = [
  { value: 'this_week', label: 'This week' },
  { value: 'last_week', label: 'Last week' },
  { value: 'this_month', label: 'This month' },
  { value: 'last_month', label: 'Last month' },
  { value: 'this_quarter', label: 'This quarter' },
  { value: 'last_quarter', label: 'Last quarter' },
  { value: 'this_year', label: 'This year' },
  { value: 'custom', label: 'Custom range' },
]

function applyPreset(val: string) {
  preset.value = val
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()

  switch (val) {
    case 'this_week': {
      const d = new Date(now)
      d.setDate(d.getDate() - d.getDay() + (d.getDay() === 0 ? -6 : 1))
      fromDate.value = d.toISOString().slice(0, 10)
      toDate.value = now.toISOString().slice(0, 10)
      break
    }
    case 'last_week': {
      const d = new Date(now)
      d.setDate(d.getDate() - d.getDay() + (d.getDay() === 0 ? -6 : 1) - 7)
      fromDate.value = d.toISOString().slice(0, 10)
      const end = new Date(d)
      end.setDate(end.getDate() + 6)
      toDate.value = end.toISOString().slice(0, 10)
      break
    }
    case 'this_month':
      fromDate.value = `${y}-${String(m + 1).padStart(2, '0')}-01`
      toDate.value = now.toISOString().slice(0, 10)
      break
    case 'last_month': {
      const lm = m === 0 ? 11 : m - 1
      const ly = m === 0 ? y - 1 : y
      fromDate.value = `${ly}-${String(lm + 1).padStart(2, '0')}-01`
      const lastDay = new Date(ly, lm + 1, 0)
      toDate.value = lastDay.toISOString().slice(0, 10)
      break
    }
    case 'this_quarter': {
      const qStart = Math.floor(m / 3) * 3
      fromDate.value = `${y}-${String(qStart + 1).padStart(2, '0')}-01`
      toDate.value = now.toISOString().slice(0, 10)
      break
    }
    case 'last_quarter': {
      let qStart = Math.floor(m / 3) * 3 - 3
      let qy = y
      if (qStart < 0) { qStart += 12; qy -= 1 }
      fromDate.value = `${qy}-${String(qStart + 1).padStart(2, '0')}-01`
      const lastDay = new Date(qy, qStart + 3, 0)
      toDate.value = lastDay.toISOString().slice(0, 10)
      break
    }
    case 'this_year':
      fromDate.value = `${y}-01-01`
      toDate.value = now.toISOString().slice(0, 10)
      break
    case 'custom':
      break
  }
}

// Expand/collapse days
const expandedDays = ref<Set<string>>(new Set())
function toggleDay(date: string) {
  if (expandedDays.value.has(date)) expandedDays.value.delete(date)
  else expandedDays.value.add(date)
}

// ── API ────────────────────────────────────────────────────────

function getCsrf(): string {
  return (
    (window as any).frappe?.csrf_token ??
    (window as any).csrf_token ??
    (window as any).dockBoot?.session?.csrf_token ??
    ''
  )
}

async function loadRange() {
  if (!fromDate.value || !toDate.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/method/watch.api.time_entry.get_range_summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': getCsrf(),
      },
      body: JSON.stringify({ from_date: fromDate.value, to_date: toDate.value }),
    })
    const json = await res.json()
    if (!res.ok) throw new Error(json?.exc_type ?? 'Request failed')
    data.value = json.message
  } catch (e: any) {
    error.value = e?.message || __('Failed to load range data')
  } finally {
    loading.value = false
  }
}

// Non-empty days for display
const activeDays = computed(() =>
  (data.value?.days ?? []).filter(d => d.entry_count > 0)
)

const totalDays = computed(() => data.value?.days?.length ?? 0)
const activeDayCount = computed(() => activeDays.value.length)

// ── Lifecycle ──────────────────────────────────────────────────

onMounted(() => loadRange())
watch([fromDate, toDate], () => { if (preset.value !== 'custom') loadRange() })

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function tagStyle(color: string | null): Record<string, string> {
  if (!color) return {}
  return { backgroundColor: color + '18', color, borderColor: color + '40' }
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <CalendarRange class="h-5 w-5 text-gray-400 dark:text-gray-500" />
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white">{{ __('Date Range Report') }}</h1>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex flex-wrap items-end gap-4 mb-6">
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('Preset') }}</label>
        <select
          :value="preset"
          class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                 px-3 py-2 text-sm text-gray-900 dark:text-white
                 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
          @change="applyPreset(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="p in PRESETS" :key="p.value" :value="p.value">{{ __(p.label) }}</option>
        </select>
      </div>

      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('From') }}</label>
        <input
          v-model="fromDate" type="date"
          class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                 px-3 py-2 text-sm text-gray-900 dark:text-white
                 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
          @change="preset = 'custom'"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ __('To') }}</label>
        <input
          v-model="toDate" type="date"
          class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                 px-3 py-2 text-sm text-gray-900 dark:text-white
                 focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
          @change="preset = 'custom'"
        />
      </div>
      <button
        :disabled="loading"
        class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
               hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
        @click="loadRange"
      >
        {{ loading ? __('Loading...') : __('Load') }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading && !data" class="flex items-center justify-center py-20">
      <div class="h-6 w-6 animate-spin rounded-full border-2 border-accent-600 border-t-transparent" />
    </div>

    <!-- Error -->
    <p v-else-if="error" class="text-sm text-red-500">{{ error }}</p>

    <!-- Results -->
    <template v-else-if="data">
      <!-- Summary cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{{ __('Total') }}</p>
          <p class="text-xl font-semibold text-gray-900 dark:text-white">{{ formatHours(data.rounded_total_hours) }}</p>
          <p v-if="data.rounded_total_hours !== data.total_hours" class="text-xs text-gray-400 dark:text-gray-500">
            {{ __('Raw') }}: {{ formatHours(data.total_hours) }}
          </p>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{{ __('Billable') }}</p>
          <p class="text-xl font-semibold text-gray-900 dark:text-white">{{ formatHours(data.rounded_billable_hours) }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{{ __('Days') }}</p>
          <p class="text-xl font-semibold text-gray-900 dark:text-white">{{ activeDayCount }}</p>
          <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('of') }} {{ totalDays }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
          <p class="text-xs text-gray-400 dark:text-gray-500 mb-1">{{ __('Avg / day') }}</p>
          <p class="text-xl font-semibold text-gray-900 dark:text-white">
            {{ activeDayCount > 0 ? formatHours(data.total_hours / activeDayCount) : '0h' }}
          </p>
        </div>
      </div>

      <!-- Tag breakdown -->
      <div v-if="data.tags.length" class="mb-6 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-3">
          {{ __('By Tag') }}
        </h2>
        <div class="space-y-2">
          <div v-for="tag in data.tags" :key="tag.tag_name ?? '__untagged__'" class="flex items-center gap-3">
            <span
              class="inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium"
              :style="tagStyle(tag.color)"
            >
              {{ tag.tag_name ?? __('Untagged') }}
            </span>
            <div class="flex-1 h-2 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
              <div
                class="h-full rounded-full"
                :style="{ width: tag.pct + '%', backgroundColor: tag.color ?? '#9ca3af' }"
              />
            </div>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-16 text-right">{{ formatHours(tag.hours) }}</span>
            <span class="text-xs text-gray-400 dark:text-gray-500 w-12 text-right">{{ tag.pct }}%</span>
          </div>
        </div>
      </div>

      <!-- Day list -->
      <div class="space-y-1">
        <div
          v-for="day in activeDays"
          :key="day.date"
          class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        >
          <button
            class="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
            @click="toggleDay(day.date)"
          >
            <component
              :is="expandedDays.has(day.date) ? ChevronDown : ChevronRight"
              class="h-4 w-4 text-gray-400 dark:text-gray-500 flex-shrink-0"
            />
            <span class="text-sm font-medium text-gray-900 dark:text-white w-32">{{ formatDate(day.date) }}</span>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ day.entry_count }} {{ day.entry_count === 1 ? __('entry') : __('entries') }}</span>
            <div class="flex-1 flex gap-1 justify-end">
              <span
                v-for="tag in day.top_tags.slice(0, 3)"
                :key="tag.tag_name"
                class="inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium"
                :style="tagStyle(tag.color)"
              >
                {{ tag.tag_name }}
              </span>
              <span v-if="day.overflow_count > 0" class="text-[10px] text-gray-400 dark:text-gray-500">+{{ day.overflow_count }}</span>
            </div>
            <span class="text-sm font-semibold text-gray-900 dark:text-white w-16 text-right">
              {{ formatHours(day.rounded_total_hours) }}
            </span>
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="activeDays.length === 0" class="py-12 text-center">
        <p class="text-sm text-gray-400 dark:text-gray-500">{{ __('No entries in this date range.') }}</p>
      </div>
    </template>
  </div>
</template>
