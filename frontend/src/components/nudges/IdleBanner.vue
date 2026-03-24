<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { CornerDownLeft, X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { formatDuration } from '@/composables/useTimer'
import type { IdlePromptData } from '@/composables/useIdleDetection'

const props = defineProps<{
  prompt: IdlePromptData
}>()

const emit = defineEmits<{
  keepAll: []
  stopAt: []
  stopNow: []
  dismiss: []
}>()

const awayLabel = computed(() => {
  const secs = Math.round(props.prompt.awayMinutes * 60)
  return formatDuration(secs)
})

const sinceLabel = computed(() => {
  const d = props.prompt.hiddenAt
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
})

const stopAtLabel = computed(() => {
  return __('Stop at {0}', [sinceLabel.value])
})
</script>

<template>
  <div
    class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
           px-4 py-3 space-y-2"
  >
    <div class="flex items-center gap-3">
      <CornerDownLeft
        class="w-4 h-4 shrink-0 text-gray-500 dark:text-slate-500"
        aria-hidden="true"
      />
      <span class="flex-1 text-sm text-gray-900 dark:text-slate-100">
        {{ __('You were away for {0}', [awayLabel]) }}
        <span class="text-gray-500 dark:text-slate-500 ml-1">
          ({{ __('since {0}', [sinceLabel]) }})
        </span>
      </span>
      <button
        type="button"
        class="p-1 rounded text-gray-500 dark:text-slate-500 hover:text-gray-900 dark:hover:text-slate-100
               hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors shrink-0"
        :title="__('Dismiss')"
        @click="emit('dismiss')"
      >
        <X class="w-4 h-4" aria-hidden="true" />
      </button>
    </div>

    <div class="flex flex-wrap items-center gap-2 pl-7">
      <button
        type="button"
        class="text-xs px-3 py-1.5 rounded-lg
               bg-[var(--app-accent-500)] text-white
               hover:opacity-90 transition-opacity"
        @click="emit('keepAll')"
      >
        {{ __('Keep all') }}
      </button>
      <button
        type="button"
        class="text-xs px-3 py-1.5 rounded-lg
               border border-gray-200 dark:border-slate-700
               text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800
               transition-colors"
        @click="emit('stopAt')"
      >
        {{ stopAtLabel }}
      </button>
      <button
        type="button"
        class="text-xs px-3 py-1.5 rounded-lg
               border border-gray-200 dark:border-slate-700
               text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800
               transition-colors"
        @click="emit('stopNow')"
      >
        {{ __('Stop now') }}
      </button>
    </div>
  </div>
</template>
