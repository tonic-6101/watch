<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { Play, Pause, Square, Pencil } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useTimer, formatElapsed, formatDuration, type EntryType } from '@/composables/useTimer'
import { useToast } from '@/composables/useToast'
import { formatHours } from '@/composables/useEntries'
import TagInput from './TagInput.vue'
import FocusWidget from './FocusWidget.vue'

type View = 'start' | 'active' | 'stop' | 'edit' | 'conflict'
type Tab  = 'timer' | 'focus'

const timer = useTimer()
const toast = useToast()

const emit = defineEmits<{
  stopped: []
}>()

// ── Tab ──────────────────────────────────────────────────────────────────

const activeTab = ref<Tab>('timer')

watch(() => timer.focusMode.value, (active) => {
  if (active) activeTab.value = 'focus'
})

function selectTab(tab: Tab) {
  if (tab === 'focus' && timer.isActive.value && !timer.focusMode.value) return
  if (tab === 'timer' && timer.focusMode.value) return
  activeTab.value = tab
}

// ── Timer view ───────────────────────────────────────────────────────────

// Derived view — follows timer state unless user is in a transient form
const view = ref<View>(timer.isStopped.value ? 'start' : 'active')

// Watch state changes from realtime / polling
watch(timer.state, (s) => {
  if (view.value !== 'stop' && view.value !== 'edit' && view.value !== 'conflict') {
    view.value = s === 'stopped' ? 'start' : 'active'
  }
})

// ── Form models ─────────────────────────────────────────────────────────

const formDesc    = ref('')
const formTags    = ref<string[]>([])
const formType    = ref<EntryType>('billable')
const stopNote    = ref('')

function openStart() {
  if (timer.isActive.value) {
    view.value = 'conflict'
    return
  }
  formDesc.value = ''
  formTags.value = []
  formType.value = 'billable'
  view.value     = 'start'
}

function openEdit() {
  formDesc.value = timer.description.value
  formTags.value = [...timer.tags.value]
  formType.value = timer.entryType.value
  view.value     = 'edit'
}

// ── Actions ──────────────────────────────────────────────────────────────

async function handleStart() {
  await timer.start(formDesc.value, formTags.value, formType.value)
  view.value = 'active'
}

async function handlePause() {
  await timer.pause()
}

async function handleResume() {
  await timer.resume()
}

async function handleOpenStop() {
  stopNote.value = ''
  view.value     = 'stop'
}

async function handleStop() {
  const result = await timer.stop(stopNote.value)
  const entry = result.entry
  const elapsed = entry._saved_elapsed ?? 0
  const entryDate = entry.date ?? ''

  // Reset to start form immediately
  view.value = 'start'
  emit('stopped')

  // Show toast with duration and link to view entry
  toast.show(
    `${__('Timer saved')} — ${formatDuration(elapsed)}`,
    {
      action: {
        label: __('View entry'),
        handler: () => { window.location.href = `/watch/daily/${entryDate}` },
      },
      duration: 5000,
    },
  )
}

async function handleStopAndStartNew() {
  const result = await timer.stop('')
  const elapsed = result.entry._saved_elapsed ?? 0
  emit('stopped')
  toast.show(`${__('Timer saved')} — ${formatDuration(elapsed)}`, { duration: 3000 })
  formDesc.value = ''
  formTags.value = []
  formType.value = 'billable'
  view.value     = 'start'
}

async function handleUpdate() {
  await timer.update(formDesc.value, formTags.value, formType.value)
  view.value = 'active'
}

// ── Budget warning ───────────────────────────────────────────────────────

interface BudgetStatus {
  used: number; budget: number; pct: number | null
  status: 'none' | 'approaching' | 'exceeded'; threshold_pct: number
}

const budgetCache = new Map<string, BudgetStatus>()
const formBudgetWarning = ref<{ tag: string; b: BudgetStatus } | null>(null)

async function checkTagBudgets(tags: string[]) {
  formBudgetWarning.value = null
  let worst: { tag: string; b: BudgetStatus } | null = null
  for (const tag of tags) {
    if (!budgetCache.has(tag)) {
      try {
        const res  = await fetch(
          `/api/method/watch.api.tags.get_budget_usage?tag_name=${encodeURIComponent(tag)}`,
          { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
        )
        const data = await res.json()
        if (data.message) budgetCache.set(tag, data.message)
      } catch { /* ignore */ }
    }
    const b = budgetCache.get(tag)
    if (b && b.status !== 'none') {
      if (!worst || (b.status === 'exceeded' && worst.b.status !== 'exceeded')) {
        worst = { tag, b }
      }
    }
  }
  formBudgetWarning.value = worst
}

watch(formTags, checkTagBudgets, { deep: true })

// ── Helpers ──────────────────────────────────────────────────────────────

const ENTRY_OPTIONS: { value: EntryType; label: string }[] = [
  { value: 'billable',     label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal',     label: 'Internal' },
]

</script>

<template>
  <div class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-4">

    <!-- ── Tabs ─────────────────────────────────────────────────── -->
    <div class="flex mb-4 border-b border-[var(--watch-border)] -mx-4 px-4">
      <button
        v-for="tab in (['timer', 'focus'] as Tab[])"
        :key="tab"
        type="button"
        :class="[
          'flex-1 pb-2 text-xs font-medium border-b-2 -mb-px transition-colors',
          activeTab === tab
            ? 'border-[var(--watch-primary)] text-[var(--watch-primary)]'
            : 'border-transparent text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]',
          (tab === 'focus' && timer.isActive.value && !timer.focusMode.value) ||
          (tab === 'timer' && timer.focusMode.value)
            ? 'opacity-40 cursor-not-allowed'
            : 'cursor-pointer',
        ]"
        @click="selectTab(tab)"
      >
        {{ tab === 'timer' ? __('Timer') : __('Focus') }}
      </button>
    </div>

    <!-- Focus tab content -->
    <FocusWidget v-if="activeTab === 'focus'" />

    <!-- Timer tab content -->
    <template v-else>

    <!-- ══════════════════════════════════════════════════════════════
         START FORM — timer stopped
         ══════════════════════════════════════════════════════════════ -->
    <div v-if="view === 'start'">
      <h2 class="text-sm font-semibold text-[var(--watch-text)] mb-3">
        {{ __('Start Timer') }}
      </h2>

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
        @keydown.enter="handleStart"
      />

      <!-- Tags -->
      <div class="mb-1">
        <TagInput v-model="formTags" />
      </div>

      <!-- Budget warning -->
      <div
        v-if="formBudgetWarning"
        class="mb-3 text-xs px-1"
        :class="formBudgetWarning.b.status === 'exceeded' ? 'text-red-500' : 'text-amber-500'"
      >
        <template v-if="formBudgetWarning.b.status === 'exceeded'">
          ⚠ {{ __('Budget exceeded') }} — {{ formatHours(formBudgetWarning.b.used) }}
          {{ __('of') }} {{ formatHours(formBudgetWarning.b.budget) }} {{ __('used this month') }}
        </template>
        <template v-else>
          ⚠ {{ formatHours(formBudgetWarning.b.used) }}
          {{ __('of') }} {{ formatHours(formBudgetWarning.b.budget) }} {{ __('used this month') }}
        </template>
      </div>
      <div v-else class="mb-3" />

      <!-- Entry type -->
      <div class="flex gap-2 mb-4">
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

      <!-- Start button -->
      <button
        class="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg
               bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
               text-white text-sm font-medium transition-colors disabled:opacity-50"
        :disabled="timer.loading.value"
        @click="handleStart"
      >
        <Play class="w-4 h-4" aria-hidden="true" />
        {{ __('Start Timer') }}
      </button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         ACTIVE — running or paused
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'active'">
      <!-- Elapsed -->
      <div class="flex items-center gap-2 mb-2">
        <span
          :class="[
            'inline-block w-2.5 h-2.5 rounded-full flex-shrink-0',
            timer.isRunning.value
              ? 'bg-[var(--timer-running)] animate-pulse'
              : 'bg-[var(--timer-paused)]',
          ]"
          aria-hidden="true"
        />
        <span class="timer-display text-2xl font-semibold text-[var(--watch-text)] tabular-nums">
          {{ formatElapsed(timer.elapsed.value) }}
        </span>
      </div>

      <!-- Description -->
      <p
        v-if="timer.description.value"
        class="text-sm text-[var(--watch-text)] mb-2 truncate"
      >
        "{{ timer.description.value }}"
      </p>

      <!-- Tags -->
      <div v-if="timer.tags.value.length" class="flex flex-wrap gap-1.5 mb-2">
        <span
          v-for="tag in timer.tags.value"
          :key="tag"
          class="px-2 py-0.5 rounded-md text-xs font-medium
                 bg-[var(--watch-primary-light)] text-[var(--watch-primary)]"
        >
          {{ tag }}
        </span>
      </div>

      <!-- Entry type badge -->
      <div class="mb-3">
        <span
          :class="[
            'px-2 py-0.5 rounded-md text-xs font-medium',
            timer.entryType.value === 'billable'
              ? 'badge-billable'
              : timer.entryType.value === 'internal'
              ? 'badge-internal'
              : 'badge-non-billable',
          ]"
        >
          {{ __(timer.entryType.value === 'billable'
            ? 'Billable'
            : timer.entryType.value === 'non-billable'
            ? 'Non-billable'
            : 'Internal') }}
        </span>
      </div>

      <!-- Controls -->
      <div class="flex gap-2">
        <!-- Pause / Resume -->
        <button
          v-if="timer.isRunning.value"
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handlePause"
        >
          <Pause class="w-4 h-4" aria-hidden="true" />
          {{ __('Pause') }}
        </button>
        <button
          v-else
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleResume"
        >
          <Play class="w-4 h-4" aria-hidden="true" />
          {{ __('Resume') }}
        </button>

        <!-- Stop -->
        <button
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleOpenStop"
        >
          <Square class="w-4 h-4" aria-hidden="true" />
          {{ __('Stop') }}
        </button>

        <!-- Edit -->
        <button
          class="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors ml-auto"
          @click="openEdit"
        >
          <Pencil class="w-3.5 h-3.5" aria-hidden="true" />
          {{ __('Edit') }}
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         STOP FORM
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'stop'">
      <h2 class="text-sm font-semibold text-[var(--watch-text)] mb-3">
        {{ __('Stop Timer') }}
      </h2>

      <textarea
        v-model="stopNote"
        :placeholder="__('Add a note… (optional)')"
        rows="2"
        class="w-full px-3 py-2 mb-3 rounded-lg border border-[var(--watch-border)]
               bg-[var(--watch-bg)] text-sm text-[var(--watch-text)]
               placeholder-[var(--watch-text-muted)] outline-none resize-none
               focus:ring-2 focus:ring-[var(--watch-primary)]/30
               focus:border-[var(--watch-primary)]"
      />

      <div class="flex gap-2">
        <button
          class="flex-1 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors"
          @click="view = 'active'"
        >
          {{ __('Cancel') }}
        </button>
        <button
          class="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg
                 bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                 text-white text-sm font-medium transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleStop"
        >
          <Square class="w-4 h-4" aria-hidden="true" />
          {{ __('Stop & Save') }}
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         EDIT FORM — update running/paused entry
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'edit'">
      <h2 class="text-sm font-semibold text-[var(--watch-text)] mb-3">
        {{ __('Edit Timer') }}
      </h2>

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

      <div class="mb-1">
        <TagInput v-model="formTags" />
      </div>

      <!-- Budget warning (edit form) -->
      <div
        v-if="formBudgetWarning"
        class="mb-3 text-xs px-1"
        :class="formBudgetWarning.b.status === 'exceeded' ? 'text-red-500' : 'text-amber-500'"
      >
        <template v-if="formBudgetWarning.b.status === 'exceeded'">
          ⚠ {{ __('Budget exceeded') }} — {{ formatHours(formBudgetWarning.b.used) }}
          {{ __('of') }} {{ formatHours(formBudgetWarning.b.budget) }} {{ __('used this month') }}
        </template>
        <template v-else>
          ⚠ {{ formatHours(formBudgetWarning.b.used) }}
          {{ __('of') }} {{ formatHours(formBudgetWarning.b.budget) }} {{ __('used this month') }}
        </template>
      </div>
      <div v-else class="mb-3" />

      <div class="flex gap-2 mb-4">
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

      <div class="flex gap-2">
        <button
          class="flex-1 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors"
          @click="view = 'active'"
        >
          {{ __('Cancel') }}
        </button>
        <button
          class="flex-1 py-2 rounded-lg bg-[var(--watch-primary)]
                 hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium
                 transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleUpdate"
        >
          {{ __('Save') }}
        </button>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════
         CONFLICT DIALOG — timer already running
         ══════════════════════════════════════════════════════════════ -->
    <div v-else-if="view === 'conflict'">
      <h2 class="text-sm font-semibold text-[var(--watch-text)] mb-1">
        {{ __('Timer already running') }}
      </h2>
      <p class="text-sm text-[var(--watch-text-secondary)] mb-4">
        {{ formatElapsed(timer.elapsed.value) }}
        <span v-if="timer.description.value"> · "{{ timer.description.value }}"</span>
      </p>

      <div class="flex gap-2">
        <button
          class="flex-1 py-2 rounded-lg border border-[var(--watch-border)]
                 text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
                 transition-colors"
          @click="view = 'active'"
        >
          {{ __('Cancel') }}
        </button>
        <button
          class="flex-1 py-2 rounded-lg bg-[var(--watch-primary)]
                 hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium
                 transition-colors disabled:opacity-50"
          :disabled="timer.loading.value"
          @click="handleStopAndStartNew"
        >
          {{ __('Stop it & start new') }}
        </button>
      </div>
    </div>

    <!-- Error banner -->
    <p
      v-if="timer.error.value"
      class="mt-3 text-xs text-red-500"
    >
      {{ timer.error.value }}
    </p>
    </template><!-- end timer tab -->

  </div>
</template>
