<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Play, Square, SkipForward, Coffee, Check } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useTimer, type EntryType } from '@/composables/useTimer'
import TagInput from './TagInput.vue'

const timer = useTimer()

// ── View ─────────────────────────────────────────────────────────────────

type FocusView = 'setup' | 'working' | 'break' | 'done'

function initialView(): FocusView {
  if (timer.focusMode.value) {
    return timer.focusPhase.value === 'break' ? 'break' : 'working'
  }
  return 'setup'
}

const view = ref<FocusView>(initialView())

// ── Form state (setup) ────────────────────────────────────────────────────

const formDesc         = ref('')
const formTags         = ref<string[]>([])
const formType         = ref<EntryType>('billable')
const formSessions     = ref(4)
const formWorkMinutes  = ref(25)
const formBreakMinutes = ref(5)

const SESSION_PRESETS = [1, 2, 4]
const WORK_PRESETS    = [15, 25, 50]
const BREAK_PRESETS   = [5, 10]

const ENTRY_OPTIONS: { value: EntryType; label: string }[] = [
  { value: 'billable',     label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal',     label: 'Internal' },
]

// ── Work countdown ────────────────────────────────────────────────────────

const workTotal     = computed(() => timer.focusWorkMinutes.value * 60)
const workRemaining = computed(() => Math.max(0, workTotal.value - timer.elapsed.value))
const workProgressPct = computed(() =>
  workTotal.value ? Math.min(100, (timer.elapsed.value / workTotal.value) * 100) : 0
)

let workEndCalled = false

watch(workRemaining, async (val) => {
  if (val === 0 && view.value === 'working' && !workEndCalled && !timer.loading.value) {
    workEndCalled = true
    await handleWorkEnd()
  }
})

// ── Break countdown (client-side) ─────────────────────────────────────────

const breakRemaining  = ref(0)
const breakTotal      = computed(() => timer.focusBreakMinutes.value * 60)
const breakProgressPct = computed(() =>
  breakTotal.value ? Math.min(100, ((breakTotal.value - breakRemaining.value) / breakTotal.value) * 100) : 0
)

let breakInterval: ReturnType<typeof setInterval> | null = null

function startBreakCountdown() {
  breakRemaining.value = timer.focusBreakMinutes.value * 60
  if (breakInterval) clearInterval(breakInterval)
  breakInterval = setInterval(() => {
    if (breakRemaining.value > 0) {
      breakRemaining.value -= 1
    } else {
      clearInterval(breakInterval!)
      breakInterval = null
      handleBreakEnd()
    }
  }, 1000)
}

function stopBreakCountdown() {
  if (breakInterval) { clearInterval(breakInterval); breakInterval = null }
}

// If the widget mounts during break phase (page reload), start the countdown
onMounted(() => {
  if (view.value === 'break') {
    startBreakCountdown()
  }
})

onUnmounted(stopBreakCountdown)

// ── External state sync ───────────────────────────────────────────────────

watch(() => timer.focusMode.value, (active) => {
  if (active && view.value === 'setup') {
    workEndCalled = false
    view.value = timer.focusPhase.value === 'break' ? 'break' : 'working'
  }
  if (!active && view.value !== 'setup') {
    stopBreakCountdown()
    view.value = 'setup'
  }
})

watch(() => timer.focusPhase.value, (phase) => {
  if (timer.focusMode.value && phase === 'break' && view.value === 'working') {
    view.value = 'break'
    startBreakCountdown()
  }
})

// ── Format helpers ────────────────────────────────────────────────────────

function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// ── Browser notifications ─────────────────────────────────────────────────

function notify(title: string, body: string) {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(title, { body })
  }
}

async function requestNotifPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    await Notification.requestPermission()
  }
}

// ── Actions ───────────────────────────────────────────────────────────────

async function handleStart() {
  await requestNotifPermission()
  workEndCalled = false
  await timer.startFocus(
    formDesc.value,
    formTags.value,
    formType.value,
    formSessions.value,
    formWorkMinutes.value,
    formBreakMinutes.value,
  )
  view.value = 'working'
}

async function handleWorkEnd() {
  const res = await timer.endFocusSession()
  if (res.completed) {
    view.value = 'done'
    notify(__('Focus complete!'), __('All sessions done. Great work!'))
  } else {
    view.value = 'break'
    notify(__('Session complete'), `${__('Break')} ${timer.focusBreakMinutes.value}m`)
    startBreakCountdown()
  }
}

async function handleBreakEnd() {
  workEndCalled = false
  await timer.skipBreak()
  view.value = 'working'
  notify(__('Break over'), __('Time to focus!'))
}

async function handleSkipBreak() {
  stopBreakCountdown()
  await handleBreakEnd()
}

async function handleEndFocus() {
  stopBreakCountdown()
  await timer.endFocus()
  view.value = 'setup'
}

function handleDone() {
  view.value = 'setup'
}
</script>

<template>
  <div>

    <!-- ══════════════════════════════════════════════════════════════
         SETUP FORM
         ══════════════════════════════════════════════════════════════ -->
    <div v-if="view === 'setup'">
      <p class="text-xs text-[var(--watch-text-muted)] mb-3">
        {{ __('Work in focused sessions with timed breaks.') }}
      </p>

      <!-- Description -->
      <input
        v-model="formDesc"
        type="text"
        :placeholder="__('What are you working on?')"
        class="w-full px-3 py-2 mb-3 rounded-lg border border-[var(--watch-border)]
               bg-[var(--watch-bg)] text-sm text-[var(--watch-text)]
               placeholder-[var(--watch-text-muted)] outline-none
               focus:ring-2 focus:ring-[var(--watch-primary)]/30
               focus:border-[var(--watch-primary)]"
      />

      <!-- Tags -->
      <div class="mb-3">
        <TagInput v-model="formTags" />
      </div>

      <!-- Entry type -->
      <div class="flex gap-1.5 mb-4">
        <button
          v-for="opt in ENTRY_OPTIONS"
          :key="opt.value"
          type="button"
          :class="[
            'flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors',
            formType === opt.value
              ? 'bg-[var(--watch-primary)] border-[var(--watch-primary)] text-white'
              : 'border-[var(--watch-border)] text-[var(--watch-text-secondary)] hover:border-[var(--watch-primary)]/50',
          ]"
          @click="formType = opt.value"
        >
          {{ __(opt.label) }}
        </button>
      </div>

      <!-- Sessions -->
      <div class="mb-3">
        <label class="block text-xs text-[var(--watch-text-muted)] mb-1.5">{{ __('Sessions') }}</label>
        <div class="flex gap-1.5">
          <button
            v-for="n in SESSION_PRESETS"
            :key="n"
            type="button"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
              formSessions === n
                ? 'bg-[var(--watch-primary)] border-[var(--watch-primary)] text-white'
                : 'border-[var(--watch-border)] text-[var(--watch-text-secondary)] hover:border-[var(--watch-primary)]/50',
            ]"
            @click="formSessions = n"
          >{{ n }}</button>
          <input
            v-model.number="formSessions"
            type="number"
            min="1"
            max="12"
            class="w-14 px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-xs text-[var(--watch-text)] outline-none
                   focus:border-[var(--watch-primary)]"
          />
        </div>
      </div>

      <!-- Work / Break -->
      <div class="flex gap-3 mb-4">
        <div class="flex-1">
          <label class="block text-xs text-[var(--watch-text-muted)] mb-1.5">{{ __('Work (min)') }}</label>
          <div class="flex gap-1.5">
            <button
              v-for="n in WORK_PRESETS"
              :key="n"
              type="button"
              :class="[
                'px-2 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                formWorkMinutes === n
                  ? 'bg-[var(--watch-primary)] border-[var(--watch-primary)] text-white'
                  : 'border-[var(--watch-border)] text-[var(--watch-text-secondary)] hover:border-[var(--watch-primary)]/50',
              ]"
              @click="formWorkMinutes = n"
            >{{ n }}</button>
          </div>
        </div>
        <div class="flex-1">
          <label class="block text-xs text-[var(--watch-text-muted)] mb-1.5">{{ __('Break (min)') }}</label>
          <div class="flex gap-1.5">
            <button
              v-for="n in BREAK_PRESETS"
              :key="n"
              type="button"
              :class="[
                'px-2 py-1.5 rounded-lg text-xs font-medium border transition-colors',
                formBreakMinutes === n
                  ? 'bg-[var(--watch-primary)] border-[var(--watch-primary)] text-white'
                  : 'border-[var(--watch-border)] text-[var(--watch-text-secondary)] hover:border-[var(--watch-primary)]/50',
              ]"
              @click="formBreakMinutes = n"
            >{{ n }}</button>
          </div>
        </div>
      </div>

      <!-- Start -->
      <button
        class="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg
               bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
               text-white text-sm font-medium transition-colors disabled:opacity-50"
        :disabled="timer.loading.value"
        @click="handleStart"
      >
        <Play class="w-4 h-4" aria-hidden="true" />
        {{ __('Start Focus') }}
      </button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         WORKING — session countdown
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'working'">

      <!-- Session indicator -->
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-medium text-[var(--watch-primary)]">
          {{ __('Session') }} {{ timer.focusSessionNumber.value }} / {{ timer.focusTotalSessions.value }}
        </span>
        <span class="inline-block w-2 h-2 rounded-full bg-[var(--timer-running)] animate-pulse" aria-hidden="true" />
      </div>

      <!-- Countdown -->
      <div class="text-center mb-3">
        <span class="text-4xl font-semibold tabular-nums text-[var(--watch-text)]">
          {{ formatCountdown(workRemaining) }}
        </span>
      </div>

      <!-- Progress bar -->
      <div class="h-1.5 rounded-full bg-[var(--watch-border)] mb-3 overflow-hidden">
        <div
          class="h-full rounded-full bg-[var(--watch-primary)] transition-all duration-1000"
          :style="{ width: `${workProgressPct}%` }"
        />
      </div>

      <!-- Description -->
      <p v-if="timer.focusDescription.value" class="text-xs text-[var(--watch-text-secondary)] truncate mb-3">
        "{{ timer.focusDescription.value }}"
      </p>

      <!-- Session dots -->
      <div class="flex justify-center gap-1.5 mb-4">
        <span
          v-for="i in timer.focusTotalSessions.value"
          :key="i"
          :class="[
            'w-2 h-2 rounded-full transition-colors',
            i < timer.focusSessionNumber.value
              ? 'bg-[var(--watch-primary)]'
              : i === timer.focusSessionNumber.value
              ? 'bg-[var(--watch-primary)] opacity-100 ring-2 ring-[var(--watch-primary)]/30'
              : 'bg-[var(--watch-border)]',
          ]"
        />
      </div>

      <!-- Abort -->
      <button
        class="w-full flex items-center justify-center gap-2 py-2 rounded-lg
               border border-[var(--watch-border)] text-sm text-[var(--watch-text-secondary)]
               hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-50"
        :disabled="timer.loading.value"
        @click="handleEndFocus"
      >
        <Square class="w-4 h-4" aria-hidden="true" />
        {{ __('End focus') }}
      </button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         BREAK
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'break'">

      <!-- Header -->
      <div class="flex items-center justify-between mb-3">
        <span class="text-xs font-medium text-[var(--watch-text-muted)]">
          {{ __('Break') }} · {{ __('Session') }} {{ timer.focusSessionNumber.value }} / {{ timer.focusTotalSessions.value }}
        </span>
        <Coffee class="w-4 h-4 text-[var(--watch-text-muted)]" aria-hidden="true" />
      </div>

      <!-- Countdown -->
      <div class="text-center mb-3">
        <span class="text-4xl font-semibold tabular-nums text-[var(--watch-text-secondary)]">
          {{ formatCountdown(breakRemaining) }}
        </span>
      </div>

      <!-- Progress bar -->
      <div class="h-1.5 rounded-full bg-[var(--watch-border)] mb-4 overflow-hidden">
        <div
          class="h-full rounded-full bg-[var(--watch-text-muted)] transition-all duration-1000"
          :style="{ width: `${breakProgressPct}%` }"
        />
      </div>

      <!-- Session dots -->
      <div class="flex justify-center gap-1.5 mb-4">
        <span
          v-for="i in timer.focusTotalSessions.value"
          :key="i"
          :class="[
            'w-2 h-2 rounded-full',
            i <= timer.focusSessionNumber.value
              ? 'bg-[var(--watch-primary)]'
              : 'bg-[var(--watch-border)]',
          ]"
        />
      </div>

      <!-- Actions -->
      <div class="flex gap-2">
        <button
          class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg
                 bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                 text-white text-sm font-medium transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleSkipBreak"
        >
          <SkipForward class="w-4 h-4" aria-hidden="true" />
          {{ __('Skip break') }}
        </button>
        <button
          class="flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                 border border-[var(--watch-border)] text-sm text-[var(--watch-text-secondary)]
                 hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleEndFocus"
        >
          <Square class="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         DONE
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'done'" class="text-center py-2">
      <div class="flex items-center justify-center w-10 h-10 rounded-full
                  bg-[var(--timer-running)] mx-auto mb-3">
        <Check class="w-5 h-5 text-white" aria-hidden="true" />
      </div>
      <p class="text-sm font-semibold text-[var(--watch-text)] mb-1">
        {{ __('Focus complete!') }}
      </p>
      <p class="text-xs text-[var(--watch-text-muted)] mb-4">
        {{ timer.focusTotalSessions.value }} {{ __('sessions done. Great work!') }}
      </p>
      <button
        class="w-full py-2 rounded-lg bg-[var(--watch-primary)]
               hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium
               transition-colors"
        @click="handleDone"
      >
        {{ __('Start new') }}
      </button>
    </div>

    <!-- Error banner -->
    <p v-if="timer.error.value" class="mt-3 text-xs text-red-500">
      {{ timer.error.value }}
    </p>

  </div>
</template>
