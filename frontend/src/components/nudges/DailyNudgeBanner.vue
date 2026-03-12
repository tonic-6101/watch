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
    class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
           px-4 py-3 flex flex-wrap items-center gap-3"
  >
    <Sun
      class="w-4 h-4 shrink-0 text-[var(--watch-text-muted)]"
      aria-hidden="true"
    />
    <span class="flex-1 text-sm text-[var(--watch-text)]">
      {{ __('No time logged yet today') }}
    </span>
    <button
      type="button"
      class="text-xs px-3 py-1.5 rounded-lg
             bg-[var(--watch-primary)] text-white
             hover:opacity-90 transition-opacity shrink-0"
      @click="emit('startTimer')"
    >
      {{ __('Start timer') }}
    </button>
    <button
      type="button"
      class="text-xs text-[var(--watch-primary)] hover:underline shrink-0"
      @click="emit('addEntry')"
    >
      {{ __('Add entry') }}
    </button>
    <button
      type="button"
      class="p-1 rounded text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]
             hover:bg-[var(--watch-bg-secondary)] transition-colors shrink-0"
      :title="__('Dismiss')"
      @click="emit('dismiss')"
    >
      <X class="w-4 h-4" aria-hidden="true" />
    </button>
  </div>
</template>
