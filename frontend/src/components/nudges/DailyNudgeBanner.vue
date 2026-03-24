<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { Sun, X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

const emit = defineEmits<{
  startTimer: []
  addEntry: []
  dismiss: []
}>()
</script>

<template>
  <div
    class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
           px-4 py-3 flex flex-wrap items-center gap-3"
  >
    <Sun
      class="w-4 h-4 shrink-0 text-gray-500 dark:text-slate-500"
      aria-hidden="true"
    />
    <span class="flex-1 text-sm text-gray-900 dark:text-slate-100">
      {{ __('No time logged yet today') }}
    </span>
    <button
      type="button"
      class="text-xs px-3 py-1.5 rounded-lg
             bg-[var(--app-accent-500)] text-white
             hover:opacity-90 transition-opacity shrink-0"
      @click="emit('startTimer')"
    >
      {{ __('Start timer') }}
    </button>
    <button
      type="button"
      class="text-xs text-[var(--app-accent-500)] hover:underline shrink-0"
      @click="emit('addEntry')"
    >
      {{ __('Add entry') }}
    </button>
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
</template>
