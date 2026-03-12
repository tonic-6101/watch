<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ChevronLeft, ChevronRight, CornerDownLeft, X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useEntries, formatHours } from '@/composables/useEntries'
import { useTimer } from '@/composables/useTimer'
import { useCurrency } from '@/composables/useCurrency'
import { useUserSettings } from '@/composables/useUserSettings'
import { useIdleDetection } from '@/composables/useIdleDetection'
import { useDailyNudge } from '@/composables/useDailyNudge'
import { useToast } from '@/composables/useToast'
import type { CreateParams, UpdateParams } from '@/composables/useEntries'
import TimerWidget from '@/components/timer/TimerWidget.vue'
import ManualEntryBar from '@/components/entries/ManualEntryBar.vue'
import EntryRow from '@/components/entries/EntryRow.vue'
import IdleBanner from '@/components/nudges/IdleBanner.vue'
import DailyNudgeBanner from '@/components/nudges/DailyNudgeBanner.vue'

// ── Props / router ───────────────────────────────────────────────────────

const props = defineProps<{
  date?: string
}>()

const router = useRouter()
const route  = useRoute()

function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

const activeDate = computed(() => props.date ?? todayStr())
const isToday    = computed(() => activeDate.value === todayStr())

function navDate(delta: number): string {
  const d = new Date(activeDate.value + 'T00:00:00')
  d.setDate(d.getDate() + delta)
  return d.toISOString().slice(0, 10)
}

function goDate(d: string) {
  if (d > todayStr()) return   // no future dates
  router.push(d === todayStr() ? '/watch' : `/watch/${d}`)
}

function formatDateLabel(d: string): string {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  })
}

// ── ManualEntryBar ref ───────────────────────────────────────────────────

const entryBarRef = ref<InstanceType<typeof ManualEntryBar> | null>(null)

function focusEntryBar() {
  nextTick(() => entryBarRef.value?.focus())
}

// ── Date picker (hidden input overlay) ──────────────────────────────────

const datePickerRef = ref<HTMLInputElement | null>(null)

function openDatePicker() {
  const el = datePickerRef.value
  if (!el) return
  el.value = activeDate.value
  if (typeof el.showPicker === 'function') {
    el.showPicker()
  } else {
    el.click()
  }
}

function onDatePickerChange(e: Event) {
  const val = (e.target as HTMLInputElement).value
  if (val) goDate(val)
}

// ── Keyboard navigation ──────────────────────────────────────────────────

function onKeyDown(e: KeyboardEvent) {
  // Skip when focus is inside an input / textarea / select / contenteditable
  const tag = (e.target as HTMLElement)?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return
  if ((e.target as HTMLElement)?.isContentEditable) return

  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    goDate(navDate(-1))
  } else if (e.key === 'ArrowRight') {
    if (!isToday.value) {
      e.preventDefault()
      goDate(navDate(1))
    }
  }
}

// ── Entries ──────────────────────────────────────────────────────────────

const entries  = useEntries()
const apiError = ref<string | null>(null)

async function loadDay() {
  await entries.load(activeDate.value)
}

watch(() => activeDate.value, loadDay)
const onFocusEntryBar = () => focusEntryBar()

onMounted(async () => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('watch:focus-entry-bar', onFocusEntryBar)
  if (route.query.focus === '1') focusEntryBar()
  loadPrefs()
  await loadDay()
  loadWeekContext()
  await checkYesterdayNudge()
  await dailyNudge.check()
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('watch:focus-entry-bar', onFocusEntryBar)
})

// ── Idle detection & daily nudge ─────────────────────────────────────────

const idle = useIdleDetection()
const dailyNudge = useDailyNudge(activeDate)

async function handleIdleStopAt() {
  await idle.stopAt()
  await loadDay()
}

async function handleIdleStopNow() {
  await idle.stopNow()
  await loadDay()
}

function handleDailyNudgeStartTimer() {
  dailyNudge.dismiss()
  // Dispatch the same event App.vue uses for the "N" shortcut
  window.dispatchEvent(new CustomEvent('watch:focus-entry-bar'))
}

function handleDailyNudgeAddEntry() {
  dailyNudge.dismiss()
  focusEntryBar()
}

// ── Timer section — "started on different day" note ─────────────────────

const timer = useTimer()

const timerDateNote = computed(() => {
  if (!timer.isActive.value || !timer.activeEntryDate.value) return null
  const entryDate = timer.activeEntryDate.value
  if (entryDate === activeDate.value) return null
  const diff = Math.round(
    (new Date(todayStr()).getTime() - new Date(entryDate).getTime()) / 86_400_000,
  )
  if (diff === 1) return __('Started yesterday')
  if (diff > 1) return __('Started {0} days ago', [diff])
  return __('Started on a different day')
})

// ── Empty-yesterday nudge ────────────────────────────────────────────────

const nudgeVisible   = ref(false)
const nudgeYesterday = ref<string | null>(null)

async function checkYesterdayNudge() {
  if (!isToday.value) return
  try {
    const res = await fetch(
      '/api/method/watch.api.time_entry.check_yesterday_empty',
      {
        headers: {
          'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
        },
      },
    )
    const data = await res.json()
    const { empty, yesterday } = data.message ?? {}
    if (!empty || !yesterday) return
    // Session-dismissed?
    const key = `watch-nudge-dismissed-${yesterday}`
    if (sessionStorage.getItem(key)) return
    nudgeYesterday.value = yesterday
    nudgeVisible.value   = true
  } catch {
    /* silently ignore nudge errors */
  }
}

function dismissNudge() {
  if (nudgeYesterday.value) {
    sessionStorage.setItem(`watch-nudge-dismissed-${nudgeYesterday.value}`, '1')
  }
  nudgeVisible.value = false
}

function goYesterday() {
  dismissNudge()
  if (nudgeYesterday.value) {
    goDate(nudgeYesterday.value)
    focusEntryBar()
  }
}

// Also dismiss if user navigates to that day manually
watch(() => activeDate.value, (d) => {
  if (d === nudgeYesterday.value) nudgeVisible.value = false
})

// ── Handlers ─────────────────────────────────────────────────────────────

async function handleBarSave(params: CreateParams) {
  apiError.value = null
  try {
    await entries.create(params)
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleTimerStarted() {
  await loadDay()
}

async function handleRowSave(name: string, params: UpdateParams) {
  apiError.value = null
  try {
    await entries.update(name, params)
  } catch (e: any) {
    apiError.value = e.message
  }
}

const toast = useToast()

async function handleRowDuplicate(name: string) {
  apiError.value = null
  try {
    const res = await fetch('/api/method/watch.api.time_entry.duplicate_entry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
      body: JSON.stringify({ entry_name: name, target_date: activeDate.value }),
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Duplicate failed')
    entries.entries.value = [data.message, ...entries.entries.value]
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleCopyToToday(name: string) {
  apiError.value = null
  const today = todayStr()
  try {
    const res = await fetch('/api/method/watch.api.time_entry.duplicate_entry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
      body: JSON.stringify({ entry_name: name, target_date: today }),
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Copy failed')
    const label = new Date(today + 'T00:00:00').toLocaleDateString(undefined, {
      weekday: 'short', day: 'numeric', month: 'short',
    })
    toast.show(__('Copied to {0}', [label]), {
      action: { label: __('View →'), handler: () => goDate(today) },
    })
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleCopyToDate(name: string, targetDate: string) {
  apiError.value = null
  try {
    const res = await fetch('/api/method/watch.api.time_entry.duplicate_entry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
      body: JSON.stringify({ entry_name: name, target_date: targetDate }),
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Copy failed')

    // If copied to current view, prepend to list
    if (targetDate === activeDate.value) {
      entries.entries.value = [data.message, ...entries.entries.value]
    } else {
      const label = new Date(targetDate + 'T00:00:00').toLocaleDateString(undefined, {
        weekday: 'short', day: 'numeric', month: 'short',
      })
      toast.show(__('Copied to {0}', [label]), {
        action: { label: __('View →'), handler: () => goDate(targetDate) },
      })
    }
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleRowDelete(name: string) {
  apiError.value = null
  try {
    await entries.remove(name)
  } catch (e: any) {
    apiError.value = e.message
  }
}

// ── Totals ────────────────────────────────────────────────────────────────

const { formatAmount } = useCurrency()

const estAmountFormatted = computed(() => {
  const amt = entries.estAmount.value
  if (!amt) return null
  return formatAmount(amt)
})

// ── Weekly target "on track" hint ────────────────────────────────────────

const { prefs, load: loadPrefs, loaded: prefsLoaded } = useUserSettings()

const weekContext = ref<{ week_total_hours: number; week_start: string; work_days: number[] } | null>(null)

async function loadWeekContext() {
  try {
    const res = await fetch(
      `/api/method/watch.api.time_entry.get_week_total?target_date=${activeDate.value}`,
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    if (res.ok && !data.exc) weekContext.value = data.message
  } catch { /* ignore */ }
}

// Reload week context when entries change (day loaded) or date changes
watch(() => entries.totalHours.value, loadWeekContext)

/** Is the viewed date today or a future day within the current ISO week? */
const isCurrentOrFutureDay = computed(() => {
  const today = todayStr()
  const d = activeDate.value
  if (d < today) return false  // past day
  if (!weekContext.value) return false
  // Check same week
  const ws = weekContext.value.week_start
  const dateObj = new Date(d + 'T00:00:00')
  const wsObj = new Date(ws + 'T00:00:00')
  const diff = (dateObj.getTime() - wsObj.getTime()) / 86_400_000
  return diff >= 0 && diff < 7
})

/** Number of configured work days remaining in the week (including today). */
const remainingWorkDays = computed(() => {
  if (!weekContext.value) return 0
  const workDays = new Set(weekContext.value.work_days)
  const today = new Date(todayStr() + 'T00:00:00')
  const wsObj = new Date(weekContext.value.week_start + 'T00:00:00')
  let count = 0
  for (let i = 0; i < 7; i++) {
    const d = new Date(wsObj)
    d.setDate(wsObj.getDate() + i)
    if (d < today) continue  // past days don't count
    const monBased = (d.getDay() + 6) % 7
    if (workDays.has(monBased)) count++
  }
  return count
})

const onTrackHint = computed(() => {
  const target = prefs.value.weekly_hour_target ?? 0
  if (!target || !prefsLoaded.value || !weekContext.value) return null
  if (!isCurrentOrFutureDay.value) return null
  if (remainingWorkDays.value <= 0) return null

  const weekLogged = weekContext.value.week_total_hours + (timer.isActive.value ? timer.elapsed.value / 3600 : 0)
  const remaining = Math.max(0, target - weekLogged)
  if (remaining <= 0) return __('Weekly target reached')

  const perDay = remaining / remainingWorkDays.value
  return `${formatHours(perDay)} ${__('remaining today to stay on track')}`
})
</script>

<template>
  <div class="min-h-screen bg-[var(--watch-bg-secondary)]">
    <div class="max-w-2xl mx-auto px-4 py-6 space-y-4">

      <!-- Nudge banners — stacking order: idle → daily → empty-yesterday -->

      <!-- 1. Idle prompt (most urgent — active timer decision) -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <IdleBanner
          v-if="idle.prompt.value"
          :prompt="idle.prompt.value"
          @keep-all="idle.keepAll"
          @stop-at="handleIdleStopAt"
          @stop-now="handleIdleStopNow"
          @dismiss="idle.dismiss"
        />
      </Transition>

      <!-- 2. Daily work nudge -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <DailyNudgeBanner
          v-if="dailyNudge.visible.value"
          @start-timer="handleDailyNudgeStartTimer"
          @add-entry="handleDailyNudgeAddEntry"
          @dismiss="dailyNudge.dismiss"
        />
      </Transition>

      <!-- 3. Empty-yesterday nudge -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 -translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 -translate-y-2"
      >
        <div
          v-if="nudgeVisible"
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
                 px-4 py-3 flex flex-wrap items-center gap-3"
        >
          <CornerDownLeft class="w-4 h-4 shrink-0 text-[var(--watch-text-muted)]" aria-hidden="true" />
          <span class="flex-1 text-sm text-[var(--watch-text)]">
            {{ __('Nothing logged yesterday') }}
            <span class="text-[var(--watch-text-muted)] ml-1">
              ({{ nudgeYesterday ? new Date(nudgeYesterday + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' }) : '' }})
            </span>
          </span>
          <button
            type="button"
            class="text-xs text-[var(--watch-primary)] hover:underline shrink-0"
            @click="goYesterday"
          >
            {{ __('Add entry for yesterday') }}
          </button>
          <button
            type="button"
            class="p-1 rounded text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]
                   hover:bg-[var(--watch-bg-secondary)] transition-colors shrink-0"
            :title="__('Dismiss')"
            @click="dismissNudge"
          >
            <X class="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </Transition>

      <!-- Timer widget -->
      <TimerWidget />

      <!-- "Started on a different day" note -->
      <p
        v-if="timerDateNote"
        class="text-xs text-[var(--watch-text-muted)] italic text-center -mt-2"
      >
        {{ timerDateNote }}
      </p>

      <!-- Date navigation -->
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="p-1.5 rounded-lg hover:bg-[var(--watch-bg)] border border-transparent
                 hover:border-[var(--watch-border)] text-[var(--watch-text-muted)]
                 hover:text-[var(--watch-text)] transition-colors"
          :title="__('Previous day')"
          @click="goDate(navDate(-1))"
        >
          <ChevronLeft class="w-5 h-5" aria-hidden="true" />
        </button>

        <!-- Date label — click to open picker -->
        <div class="relative flex-1 text-center">
          <button
            type="button"
            class="text-sm font-semibold text-[var(--watch-text)]
                   hover:text-[var(--watch-primary)] transition-colors"
            :title="__('Jump to date')"
            @click="openDatePicker"
          >
            {{ formatDateLabel(activeDate) }}
          </button>
          <!-- Hidden date input -->
          <input
            ref="datePickerRef"
            type="date"
            :max="todayStr()"
            class="absolute inset-0 opacity-0 pointer-events-none w-full h-full"
            tabindex="-1"
            aria-hidden="true"
            @change="onDatePickerChange"
          />
        </div>

        <!-- › forward arrow — disabled on today -->
        <button
          type="button"
          class="p-1.5 rounded-lg border border-transparent transition-colors"
          :class="isToday
            ? 'text-[var(--watch-border)] cursor-not-allowed'
            : 'hover:bg-[var(--watch-bg)] hover:border-[var(--watch-border)] text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]'"
          :disabled="isToday"
          :title="isToday ? undefined : __('Next day')"
          @click="!isToday && goDate(navDate(1))"
        >
          <ChevronRight class="w-5 h-5" aria-hidden="true" />
        </button>

        <!-- Today link — hidden on today -->
        <button
          v-if="!isToday"
          type="button"
          class="text-xs text-[var(--watch-primary)] hover:underline shrink-0"
          @click="goDate(todayStr())"
        >
          {{ __('Today') }}
        </button>
      </div>

      <!-- Quick entry bar -->
      <ManualEntryBar
        ref="entryBarRef"
        :date="activeDate"
        @save="handleBarSave"
        @timer-started="handleTimerStarted"
      />

      <!-- API error -->
      <p v-if="apiError" class="text-sm text-red-500 px-1">{{ apiError }}</p>

      <!-- Entry list -->
      <div class="space-y-2">
        <!-- Loading skeleton -->
        <template v-if="entries.loading.value && !entries.entries.value.length">
          <div
            v-for="i in 3"
            :key="i"
            class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
                   p-4 animate-pulse"
          >
            <div class="h-3 bg-[var(--watch-border)] rounded w-1/4 mb-2" />
            <div class="h-4 bg-[var(--watch-border)] rounded w-3/4" />
          </div>
        </template>

        <!-- Empty state -->
        <div
          v-else-if="!entries.loading.value && !entries.entries.value.length"
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
                 p-8 text-center space-y-3"
        >
          <p class="text-sm text-[var(--watch-text-muted)]">
            {{ __('No entries for') }} {{ formatDateLabel(activeDate) }}
          </p>
          <button
            type="button"
            class="text-sm text-[var(--watch-primary)] hover:underline"
            @click="focusEntryBar"
          >
            {{ __('+ Add your first entry') }}
          </button>
        </div>

        <!-- Rows -->
        <EntryRow
          v-for="entry in entries.entries.value"
          :key="entry.name"
          :entry="entry"
          :is-today="isToday"
          @save="handleRowSave"
          @duplicate="handleRowDuplicate"
          @copy-to-today="handleCopyToToday"
          @copy-to-date="handleCopyToDate"
          @delete="handleRowDelete"
          @refresh="loadDay"
        />
      </div>

      <!-- Daily totals bar -->
      <div
        v-if="entries.entries.value.length"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
               px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-sm"
      >
        <span class="text-[var(--watch-text-muted)]">
          {{ __('Total') }}
          <strong class="text-[var(--watch-text)] ml-1">
            {{ formatHours(entries.totalHours.value) }}
          </strong>
        </span>

        <span v-if="entries.billableHours.value" class="text-[var(--watch-text-muted)]">
          {{ __('Billable') }}
          <strong class="text-[var(--watch-text)] ml-1">
            {{ formatHours(entries.billableHours.value) }}
          </strong>
        </span>

        <span v-if="estAmountFormatted" class="text-[var(--watch-text-muted)]">
          {{ __('Est.') }}
          <strong class="text-[var(--watch-text)] ml-1">{{ estAmountFormatted }} €</strong>
        </span>
      </div>

      <!-- Weekly target "on track" hint -->
      <p
        v-if="onTrackHint"
        class="text-xs text-[var(--watch-text-muted)] italic px-1 -mt-2"
      >
        {{ onTrackHint }}
      </p>

    </div>
  </div>
</template>
