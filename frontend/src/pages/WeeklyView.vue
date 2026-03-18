<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp, Plus } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useEntries, formatHours } from '@/composables/useEntries'
import type { CreateParams, UpdateParams } from '@/composables/useEntries'
import { useUserSettings } from '@/composables/useUserSettings'
import { useTimer } from '@/composables/useTimer'
import WeeklyDonut from '@/components/WeeklyDonut.vue'
import WeeklyBarChart from '@/components/WeeklyBarChart.vue'
import EntryRow from '@/components/entries/EntryRow.vue'
import ManualEntryBar from '@/components/entries/ManualEntryBar.vue'
import type { TagSegment } from '@/components/WeeklyDonut.vue'
import type { DailyBar } from '@/components/WeeklyBarChart.vue'

// ── Props / router ───────────────────────────────────────────────────────

const props = defineProps<{
  week?: string   // "2026-W11"
}>()

const router = useRouter()
const route  = useRoute()
const { prefs, loaded: prefsLoaded, load: loadPrefs } = useUserSettings()
const timer = useTimer()

// ── Week helpers ─────────────────────────────────────────────────────────

function localDateStr(d: Date): string {
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function todayStr(): string {
  return localDateStr(new Date())
}

/** ISO week string → Monday date string */
function weekToMonday(w: string): string {
  const m = w.match(/^(\d{4})-W(\d{1,2})$/)
  if (!m) return todayMonday()
  const year = parseInt(m[1])
  const week = parseInt(m[2])
  // Jan 4 is always in week 1
  const jan4 = new Date(year, 0, 4)
  const dayOfWeek = jan4.getDay() || 7   // 1=Mon…7=Sun
  const monday = new Date(jan4)
  monday.setDate(jan4.getDate() - (dayOfWeek - 1) + (week - 1) * 7)
  return localDateStr(monday)
}

/** Date string → ISO week string "YYYY-WWW" */
function dateToWeek(d: string): string {
  const date = new Date(d + 'T00:00:00')
  // Thursday in current week decides the year
  const thu = new Date(date)
  thu.setDate(date.getDate() - ((date.getDay() + 6) % 7) + 3)
  const year = thu.getFullYear()
  const jan4 = new Date(year, 0, 4)
  const weekNum = Math.ceil(
    ((thu.getTime() - jan4.getTime()) / 86_400_000 + ((jan4.getDay() + 6) % 7) + 1) / 7,
  )
  return `${year}-W${String(weekNum).padStart(2, '0')}`
}

function todayMonday(): string {
  const d = new Date(todayStr() + 'T00:00:00')
  const offset = (d.getDay() + 6) % 7   // 0=Mon
  d.setDate(d.getDate() - offset)
  return localDateStr(d)
}

function currentWeek(): string {
  return dateToWeek(todayStr())
}

const activeWeek   = computed(() => (route.params.week as string) || currentWeek())
const activeMonday = computed(() => weekToMonday(activeWeek.value))
const isThisWeek   = computed(() => activeWeek.value === currentWeek())

function weekLabel(monday: string): string {
  const mon = new Date(monday + 'T00:00:00')
  const fri = new Date(monday + 'T00:00:00')
  fri.setDate(mon.getDate() + 4)
  const wm = activeWeek.value.match(/W(\d+)/)
  const weekNum = wm ? wm[1] : '?'
  const monStr = mon.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })
  const friStr = fri.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
  return `${__('Week')} ${weekNum} — ${monStr} – ${friStr}`
}

function addWeeks(w: string, delta: number): string {
  const monday = new Date(weekToMonday(w) + 'T00:00:00')
  monday.setDate(monday.getDate() + delta * 7)
  return dateToWeek(localDateStr(monday))
}

function goWeek(w: string) {
  if (w > currentWeek()) return
  router.push(w === currentWeek() ? '/watch/week' : `/watch/week/${w}`)
}

// ── Keyboard navigation ──────────────────────────────────────────────────

function onKeyDown(e: KeyboardEvent) {
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  if ((e.target as HTMLElement)?.isContentEditable) return
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    goWeek(addWeeks(activeWeek.value, -1))
  } else if (e.key === 'ArrowRight' && !isThisWeek.value) {
    e.preventDefault()
    goWeek(addWeeks(activeWeek.value, 1))
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  loadWeek()
  loadPrefs()
})
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))

// ── Week summary data ─────────────────────────────────────────────────────

interface DayData {
  date: string
  total_hours: number
  billable_hours: number
  entry_count: number
  top_tags: Array<{ name: string; tag_name: string; color: string | null; category: string | null }>
  overflow_count: number
}

interface WeekData {
  week_start: string
  week_end: string
  days: DayData[]
  total_hours: number
  billable_hours: number
  prev_week_total_hours: number
  work_days: number[]
}

const weekData = ref<WeekData | null>(null)
const loading  = ref(false)
const error    = ref<string | null>(null)

async function loadWeek() {
  loading.value = true
  error.value   = null
  try {
    const res = await fetch(
      `/api/method/watch.api.time_entry.get_weekly_summary?week_start=${activeMonday.value}`,
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Failed to load')
    weekData.value = data.message
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

watch(() => activeWeek.value, () => {
  expandedDays.value = new Set()
  dayEntries.clear()
  loadWeek()
  loadChartData()
})

// ── Chart data ────────────────────────────────────────────────────────────

interface ChartData {
  daily:       DailyBar[]
  tags:        TagSegment[]
  total_hours: number
}

const chartData    = ref<ChartData | null>(null)
const chartLoading = ref(false)

const CHART_OPEN_KEY = 'watch-chart-open'
const chartOpen = ref(localStorage.getItem(CHART_OPEN_KEY) === 'true')

function toggleChart() {
  chartOpen.value = !chartOpen.value
  localStorage.setItem(CHART_OPEN_KEY, String(chartOpen.value))
}

async function loadChartData() {
  chartLoading.value = true
  try {
    const res = await fetch(
      `/api/method/watch.api.time_entry.get_weekly_chart_data?week_start=${activeMonday.value}`,
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    if (!res.ok || data.exc) return
    chartData.value = data.message
  } finally {
    chartLoading.value = false
  }
}

onMounted(() => loadChartData())

// ── Chart click handlers ──────────────────────────────────────────────────

function onDonutClickTag(tagName: string | null) {
  if (tagName === null) {
    router.push('/watch/prepare')
  } else {
    router.push({ path: '/watch/prepare', query: { tag: tagName } })
  }
}

function onBarClickDay(day: string) {
  router.push(`/watch/${day}`)
}

// Daily target line: weekly target ÷ number of work days
const dailyTarget = computed<number | undefined>(() => {
  const target = prefs.value.weekly_hour_target ?? 0
  if (!target || !prefsLoaded.value) return undefined
  const workDays = weekData.value?.work_days?.length ?? 5
  return target / Math.max(1, workDays)
})

// ── Weekend handling ─────────────────────────────────────────────────────

const WORK_DAYS_KEY = 'watch-show-weekends'
const showWeekends = ref(localStorage.getItem(WORK_DAYS_KEY) === 'true')

function toggleWeekends() {
  showWeekends.value = !showWeekends.value
  localStorage.setItem(WORK_DAYS_KEY, String(showWeekends.value))
}

/** Non-work day integers (0=Mon…6=Sun) derived from settings. */
const nonWorkDays = computed<Set<number>>(() => {
  const workDays = weekData.value?.work_days ?? [0, 1, 2, 3, 4]
  const all = [0, 1, 2, 3, 4, 5, 6]
  return new Set(all.filter(d => !workDays.includes(d)))
})

function isWeekend(dateStr: string): boolean {
  const d = new Date(dateStr + 'T00:00:00')
  // JS getDay(): 0=Sun…6=Sat → convert to Mon-based: (getDay()+6)%7
  const monBased = (d.getDay() + 6) % 7
  return nonWorkDays.value.has(monBased)
}

const days = computed<DayData[]>(() => {
  if (!weekData.value) return []
  return weekData.value.days
})

const weekendDays = computed(() => days.value.filter(d => isWeekend(d.date)))
const weekendHasEntries = computed(() => weekendDays.value.some(d => d.entry_count > 0))

const visibleDays = computed<(DayData | 'weekend-collapse')[]>(() => {
  const result: (DayData | 'weekend-collapse')[] = []
  let collapsedAdded = false
  for (const d of days.value) {
    if (isWeekend(d.date)) {
      if (showWeekends.value || weekendHasEntries.value) {
        result.push(d)
      } else if (!collapsedAdded) {
        result.push('weekend-collapse')
        collapsedAdded = true
      }
    } else {
      result.push(d)
    }
  }
  return result
})

// ── Progress bars (day rows) ─────────────────────────────────────────────

const maxDayHours = computed(() => {
  if (!weekData.value) return 1
  return Math.max(1, ...weekData.value.days.map(d => d.total_hours))
})

function dayBarPercent(hours: number): number {
  return Math.min(100, Math.round((hours / maxDayHours.value) * 100))
}

// ── Weekly target progress ────────────────────────────────────────────────

const weeklyTarget = computed(() => prefs.value.weekly_hour_target ?? 0)
const hasTarget = computed(() => prefsLoaded.value && weeklyTarget.value > 0)

/** Total logged hours + running timer elapsed (if current week). */
const targetLogged = computed(() => {
  const base = weekData.value?.total_hours ?? 0
  if (!isThisWeek.value || !timer.isActive.value) return base
  return base + timer.elapsed.value / 3600
})

const targetPct = computed(() => {
  if (!weeklyTarget.value) return 0
  return Math.round((targetLogged.value / weeklyTarget.value) * 100)
})

const targetBarWidth = computed(() => Math.min(100, targetPct.value))

const targetColor = computed(() => {
  const pct = targetPct.value
  if (pct >= 110) return 'amber'
  if (pct >= 100) return 'green'
  if (pct >= 75)  return 'amber'
  return 'blue'
})

const targetBarClass = computed(() => {
  switch (targetColor.value) {
    case 'green': return 'bg-green-500'
    case 'amber': return 'bg-amber-500'
    default:      return 'bg-blue-500'
  }
})

const targetLabel = computed(() => {
  const logged = formatHours(targetLogged.value)
  const target = formatHours(weeklyTarget.value)
  const pct = targetPct.value
  if (pct >= 110) {
    const over = formatHours(targetLogged.value - weeklyTarget.value)
    return `${logged} / ${target} — ${over} ${__('over target')}`
  }
  if (pct >= 100) return `${logged} / ${target} — ${__('target reached')}`
  if (pct >= 75)  return `${logged} / ${target} — ${__('almost there')}`
  return `${logged} / ${target} (${pct}%)`
})

const targetTextClass = computed(() => {
  switch (targetColor.value) {
    case 'green': return 'text-green-600 dark:text-green-400'
    case 'amber': return 'text-amber-600 dark:text-amber-400'
    default:      return 'text-blue-600 dark:text-blue-400'
  }
})

// ── Formatting helpers ────────────────────────────────────────────────────

function formatDayLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
}

function isToday(dateStr: string): boolean {
  return dateStr === todayStr()
}

function chipStyle(color: string | null) {
  const c = color || 'var(--watch-primary)'
  return { backgroundColor: `${c}22`, color: c, borderColor: `${c}44` }
}

function weekendLabel(): string {
  const sat = weekendDays.value.find(d => new Date(d.date + 'T00:00:00').getDay() === 6)
  const sun = weekendDays.value.find(d => new Date(d.date + 'T00:00:00').getDay() === 0)
  if (sat && sun) {
    const s = new Date(sat.date + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
    const e = new Date(sun.date + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })
    return `${s} – ${e}`
  }
  return __('Weekend')
}

// ── Day expansion ──────────────────────────────────────────────────────

const expandedDays = ref<Set<string>>(new Set())
const dayEntries = new Map<string, ReturnType<typeof useEntries>>()

function getOrCreateDayEntries(date: string) {
  if (!dayEntries.has(date)) {
    dayEntries.set(date, useEntries())
  }
  return dayEntries.get(date)!
}

function isDayExpanded(date: string): boolean {
  return expandedDays.value.has(date)
}

async function toggleDay(date: string) {
  if (expandedDays.value.has(date)) {
    const next = new Set(expandedDays.value)
    next.delete(date)
    expandedDays.value = next
  } else {
    const next = new Set(expandedDays.value)
    next.add(date)
    expandedDays.value = next
    const de = getOrCreateDayEntries(date)
    if (!de.entries.value.length && !de.loading.value) {
      await de.load(date)
      syncDayToWeekData(date)
    }
  }
}

function syncDayToWeekData(date: string) {
  const de = dayEntries.get(date)
  if (!de || !weekData.value) return
  const day = weekData.value.days.find(d => d.date === date)
  if (!day) return
  day.total_hours = de.totalHours.value
  day.billable_hours = de.billableHours.value
  day.entry_count = de.entries.value.length
  weekData.value.total_hours = weekData.value.days.reduce((s, d) => s + d.total_hours, 0)
  weekData.value.billable_hours = weekData.value.days.reduce((s, d) => s + d.billable_hours, 0)
}

async function handleDayBarSave(date: string, params: CreateParams) {
  const de = getOrCreateDayEntries(date)
  await de.create(params)
  syncDayToWeekData(date)
  loadChartData()
}

async function handleDayRowSave(date: string, name: string, params: UpdateParams) {
  const de = getOrCreateDayEntries(date)
  await de.update(name, params)
  syncDayToWeekData(date)
  loadChartData()
}

async function handleDayRowDelete(date: string, name: string) {
  const de = getOrCreateDayEntries(date)
  await de.remove(name)
  syncDayToWeekData(date)
  loadChartData()
}

async function handleDayRowDuplicate(date: string, name: string) {
  const res = await fetch('/api/method/watch.api.time_entry.duplicate_entry', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
    body: JSON.stringify({ entry_name: name, target_date: date }),
  })
  const data = await res.json()
  if (!res.ok || data.exc) return
  const de = getOrCreateDayEntries(date)
  de.entries.value = [data.message, ...de.entries.value]
  syncDayToWeekData(date)
  loadChartData()
}

async function handleDayCopyToDate(sourceDate: string, name: string, targetDate: string) {
  const res = await fetch('/api/method/watch.api.time_entry.duplicate_entry', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
    body: JSON.stringify({ entry_name: name, target_date: targetDate }),
  })
  const data = await res.json()
  if (!res.ok || data.exc) return
  // If target day is expanded in this week, add the entry
  if (dayEntries.has(targetDate) && expandedDays.value.has(targetDate)) {
    const de = getOrCreateDayEntries(targetDate)
    de.entries.value = [data.message, ...de.entries.value]
    syncDayToWeekData(targetDate)
  }
  loadChartData()
}
</script>

<template>
  <div class="min-h-screen bg-[var(--watch-bg-secondary)]">
    <div class="max-w-2xl mx-auto px-4 py-6 space-y-4">

      <!-- Week navigation -->
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="p-1.5 rounded-lg hover:bg-[var(--watch-bg)] border border-transparent
                 hover:border-[var(--watch-border)] text-[var(--watch-text-muted)]
                 hover:text-[var(--watch-text)] transition-colors"
          :title="__('Previous week')"
          @click="goWeek(addWeeks(activeWeek, -1))"
        >
          <ChevronLeft class="w-5 h-5" aria-hidden="true" />
        </button>

        <span class="flex-1 text-center text-sm font-semibold text-[var(--watch-text)]">
          {{ weekLabel(activeMonday) }}
        </span>

        <button
          type="button"
          class="p-1.5 rounded-lg border border-transparent transition-colors"
          :class="isThisWeek
            ? 'text-[var(--watch-border)] cursor-not-allowed'
            : 'hover:bg-[var(--watch-bg)] hover:border-[var(--watch-border)] text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]'"
          :disabled="isThisWeek"
          :title="isThisWeek ? undefined : __('Next week')"
          @click="!isThisWeek && goWeek(addWeeks(activeWeek, 1))"
        >
          <ChevronRight class="w-5 h-5" aria-hidden="true" />
        </button>

        <button
          v-if="!isThisWeek"
          type="button"
          class="text-xs text-[var(--watch-primary)] hover:underline shrink-0"
          @click="goWeek(currentWeek())"
        >
          {{ __('This week') }}
        </button>
      </div>

      <!-- Weekly target progress bar -->
      <div
        v-if="hasTarget && weekData"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] px-4 py-3 space-y-1.5"
      >
        <div class="h-2.5 rounded-full bg-[var(--watch-border)] overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300"
            :class="targetBarClass"
            :style="{ width: targetBarWidth + '%' }"
          />
        </div>
        <p class="text-xs font-medium" :class="targetTextClass">
          {{ targetLabel }}
        </p>
      </div>

      <!-- Error -->
      <p v-if="error" class="text-sm text-red-500 px-1">{{ error }}</p>

      <!-- Loading skeleton -->
      <div v-if="loading && !weekData" class="space-y-2">
        <div
          v-for="i in 5"
          :key="i"
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-3 animate-pulse"
        >
          <div class="h-4 bg-[var(--watch-border)] rounded w-1/3" />
        </div>
      </div>

      <template v-else-if="weekData">

        <!-- Day rows card -->
        <div
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] divide-y
                 divide-[var(--watch-border)]"
        >
          <template v-for="row in visibleDays" :key="typeof row === 'string' ? 'collapse' : row.date">

            <!-- Weekend collapsed row -->
            <div
              v-if="row === 'weekend-collapse'"
              class="px-4 py-2 flex items-center gap-3 opacity-40 cursor-default"
            >
              <span class="text-xs text-[var(--watch-text-muted)] w-20 shrink-0">
                {{ weekendLabel() }}
              </span>
              <div class="flex-1 h-1.5 rounded-full bg-[var(--watch-border)]" />
            </div>

            <!-- Day wrapper (summary + expansion) -->
            <div v-else>
              <!-- Summary row -->
              <div
                class="px-4 py-3 flex items-center gap-3 cursor-pointer transition-colors"
                :class="[
                  isToday(row.date)
                    ? 'bg-[var(--watch-primary)]/5'
                    : 'hover:bg-[var(--watch-bg-secondary)]',
                ]"
                @click="toggleDay(row.date)"
              >
                <!-- Day label -->
                <span
                  class="text-xs font-medium shrink-0 w-16"
                  :class="isToday(row.date) ? 'text-[var(--watch-primary)]' : 'text-[var(--watch-text-muted)]'"
                >
                  {{ formatDayLabel(row.date) }}
                </span>

                <!-- Progress bar -->
                <div class="relative flex-1 h-2 rounded-full bg-[var(--watch-border)] overflow-hidden">
                  <template v-if="row.entry_count > 0">
                    <div
                      class="absolute inset-y-0 left-0 rounded-full bg-[var(--watch-primary)]/70 transition-all"
                      :style="{ width: dayBarPercent(row.total_hours) + '%' }"
                    />
                  </template>
                  <template v-else>
                    <div
                      class="absolute inset-0 rounded-full"
                      style="background: repeating-linear-gradient(
                        90deg,
                        var(--watch-border) 0,
                        var(--watch-border) 4px,
                        transparent 4px,
                        transparent 8px
                      )"
                    />
                  </template>
                </div>

                <!-- Hours or dash -->
                <span class="text-xs tabular-nums shrink-0 w-12 text-right"
                      :class="row.entry_count > 0 ? 'text-[var(--watch-text)]' : 'text-[var(--watch-text-muted)]'"
                >
                  {{ row.entry_count > 0 ? formatHours(row.total_hours) : '—' }}
                </span>

                <!-- Tag chips / no-entries label -->
                <div class="flex items-center gap-1 flex-1 min-w-0 justify-end">
                  <template v-if="row.entry_count > 0 && !isDayExpanded(row.date)">
                    <span
                      v-for="tag in row.top_tags"
                      :key="tag.name || tag.tag_name"
                      class="px-1.5 py-0.5 rounded border text-xs font-medium shrink-0"
                      :style="chipStyle(tag.color)"
                    >
                      {{ tag.tag_name }}
                    </span>
                    <span
                      v-if="row.overflow_count > 0"
                      class="px-1.5 py-0.5 rounded text-xs text-[var(--watch-text-muted)]
                             bg-[var(--watch-bg-secondary)] shrink-0"
                    >
                      +{{ row.overflow_count }}
                    </span>
                  </template>
                  <template v-else-if="row.entry_count === 0 && !isDayExpanded(row.date)">
                    <span class="text-xs text-[var(--watch-text-muted)] italic mr-1">
                      {{ isToday(row.date) ? __('no entries yet') : __('no entries') }}
                    </span>
                  </template>
                </div>

                <!-- Expand/collapse chevron -->
                <ChevronUp
                  v-if="isDayExpanded(row.date)"
                  class="w-4 h-4 text-[var(--watch-text-muted)] shrink-0"
                  aria-hidden="true"
                />
                <ChevronDown
                  v-else
                  class="w-4 h-4 text-[var(--watch-text-muted)] shrink-0"
                  aria-hidden="true"
                />
              </div>

              <!-- Expansion panel -->
              <div
                v-if="isDayExpanded(row.date)"
                class="border-t border-[var(--watch-border)] bg-[var(--watch-bg-secondary)]/50 px-3 py-3 space-y-2"
              >
                <!-- Loading skeleton -->
                <template v-if="getOrCreateDayEntries(row.date).loading.value && !getOrCreateDayEntries(row.date).entries.value.length">
                  <div
                    v-for="i in 2"
                    :key="i"
                    class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-4 animate-pulse"
                  >
                    <div class="h-3 bg-[var(--watch-border)] rounded w-1/4 mb-2" />
                    <div class="h-4 bg-[var(--watch-border)] rounded w-3/4" />
                  </div>
                </template>

                <!-- Entry rows -->
                <template v-else>
                  <p
                    v-if="!getOrCreateDayEntries(row.date).entries.value.length"
                    class="text-xs text-[var(--watch-text-muted)] italic text-center py-2"
                  >
                    {{ __('No entries yet — add one below.') }}
                  </p>
                  <EntryRow
                    v-for="entry in getOrCreateDayEntries(row.date).entries.value"
                    :key="entry.name"
                    :entry="entry"
                    :is-today="isToday(row.date)"
                    @save="(name: string, params: UpdateParams) => handleDayRowSave(row.date, name, params)"
                    @duplicate="(name: string) => handleDayRowDuplicate(row.date, name)"
                    @copy-to-today="(name: string) => handleDayCopyToDate(row.date, name, todayStr())"
                    @copy-to-date="(name: string, date: string) => handleDayCopyToDate(row.date, name, date)"
                    @delete="(name: string) => handleDayRowDelete(row.date, name)"
                    @refresh="() => getOrCreateDayEntries(row.date).load(row.date)"
                  />
                </template>

                <!-- Add entry bar -->
                <ManualEntryBar
                  :date="row.date"
                  @save="(params: CreateParams) => handleDayBarSave(row.date, params)"
                />
              </div>
            </div>
          </template>
        </div>

        <!-- ── Chart section ──────────────────────────────────────────── -->
        <div class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden">

          <!-- Collapsible header -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-4 py-3
                   text-sm font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)]
                   transition-colors"
            @click="toggleChart"
          >
            <span>{{ __('This week at a glance') }}</span>
            <ChevronDown v-if="!chartOpen" class="w-4 h-4 text-[var(--watch-text-muted)]" aria-hidden="true" />
            <ChevronUp   v-else            class="w-4 h-4 text-[var(--watch-text-muted)]" aria-hidden="true" />
          </button>

          <!-- Charts (shown when expanded) -->
          <div v-if="chartOpen" class="border-t border-[var(--watch-border)]">
            <div v-if="chartLoading && !chartData" class="flex items-center justify-center h-32">
              <div class="w-5 h-5 border-2 border-[var(--watch-primary)] border-t-transparent
                          rounded-full animate-spin" />
            </div>
            <div v-else-if="chartData" class="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4">

              <!-- Donut: tag breakdown -->
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide
                           text-[var(--watch-text-muted)] mb-3">
                  {{ __('Time by tag') }}
                </p>
                <WeeklyDonut
                  :tags="chartData.tags"
                  :total-hours="chartData.total_hours"
                  @click-tag="onDonutClickTag"
                />
              </div>

              <!-- Bar: hours per day -->
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide
                           text-[var(--watch-text-muted)] mb-3">
                  {{ __('Hours per day') }}
                </p>
                <WeeklyBarChart
                  :daily="chartData.daily"
                  :total-hours="chartData.total_hours"
                  :target-hours-per-day="dailyTarget"
                  @click-day="onBarClickDay"
                />
              </div>

            </div>
          </div>
        </div>

        <!-- Week totals row (moved outside day rows card) -->
        <div class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
                    px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-1">
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <span class="text-xs font-semibold text-[var(--watch-text-muted)] shrink-0">
              {{ __('Week') }}
            </span>
            <div class="flex-1 h-2 rounded-full bg-[var(--watch-border)] overflow-hidden">
              <div
                class="h-full rounded-full bg-[var(--watch-primary)]/50"
                :style="{
                  width: Math.min(100, Math.round(
                    (weekData.total_hours / Math.max(1, weekData.prev_week_total_hours)) * 100
                  )) + '%'
                }"
              />
            </div>
          </div>
          <span class="text-sm font-semibold text-[var(--watch-text)] shrink-0">
            {{ formatHours(weekData.total_hours) }}
          </span>
          <span v-if="weekData.billable_hours" class="text-xs text-[var(--watch-text-muted)] shrink-0">
            {{ __('Billable') }}
            <strong class="text-[var(--watch-text)] ml-1">{{ formatHours(weekData.billable_hours) }}</strong>
          </span>
        </div>

      </template>

      <!-- Show/hide weekends toggle -->
      <div class="flex justify-end">
        <button
          type="button"
          class="text-xs text-[var(--watch-text-muted)] hover:text-[var(--watch-text)] transition-colors"
          @click="toggleWeekends"
        >
          {{ showWeekends ? __('Hide weekends') : __('Show weekends') }}
        </button>
      </div>

    </div>
  </div>
</template>
