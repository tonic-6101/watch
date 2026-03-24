<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { Pause, Play, Square } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useTimer, formatElapsed, formatDuration } from '@/composables/useTimer'
import { useToast } from '@/composables/useToast'

const emit = defineEmits<{
  stopped: []
}>()

const timer = useTimer()
const toast = useToast()

async function handlePauseResume() {
  if (timer.isRunning.value) {
    await timer.pause()
  } else {
    await timer.resume()
  }
}

async function handleStop() {
  const result = await timer.stop('')
  const elapsed = result.entry._saved_elapsed ?? 0
  const entryDate = result.entry.date ?? ''
  emit('stopped')
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
</script>

<template>
  <div
    v-if="timer.isActive.value"
    class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
           px-4 py-3 space-y-2"
  >
    <!-- Row 1: status dot + elapsed + description + tags -->
    <div class="flex items-center gap-3 min-w-0">
      <span
        :class="[
          'inline-block w-2.5 h-2.5 rounded-full shrink-0',
          timer.isRunning.value
            ? 'bg-green-500 animate-pulse'
            : 'bg-gray-500 dark:bg-slate-500',
        ]"
        aria-hidden="true"
      />

      <span class="text-lg font-semibold text-gray-900 dark:text-slate-100 tabular-nums font-mono shrink-0">
        {{ formatElapsed(timer.elapsed.value) }}
      </span>

      <span
        v-if="timer.description.value"
        class="text-sm text-gray-900 dark:text-slate-100 truncate min-w-0"
      >
        &ldquo;{{ timer.description.value }}&rdquo;
      </span>

      <div v-if="timer.tags.value.length" class="flex flex-wrap gap-1 shrink-0 ml-auto">
        <span
          v-for="tag in timer.tags.value"
          :key="tag"
          class="px-2 py-0.5 rounded-md text-xs font-medium
                 bg-[var(--app-accent-500)]/10 text-[var(--app-accent-500)]"
        >
          {{ tag }}
        </span>
      </div>
    </div>

    <!-- Row 2: controls -->
    <div class="flex items-center gap-2 pl-[22px]">
      <button
        type="button"
        class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg
               border border-gray-200 dark:border-slate-700
               text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800
               transition-colors"
        @click="handlePauseResume"
      >
        <Pause v-if="timer.isRunning.value" class="w-3.5 h-3.5" aria-hidden="true" />
        <Play v-else class="w-3.5 h-3.5" aria-hidden="true" />
        {{ timer.isRunning.value ? __('Pause') : __('Resume') }}
      </button>

      <button
        type="button"
        class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg
               bg-[var(--app-accent-500)] text-white
               hover:opacity-90 transition-opacity"
        @click="handleStop"
      >
        <Square class="w-3.5 h-3.5" aria-hidden="true" />
        {{ __('Stop') }}
      </button>
    </div>
  </div>
</template>
