<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

const emit = defineEmits<{ close: [] }>()

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' || e.key === 'h' || e.key === 'H') {
    e.preventDefault()
    emit('close')
  }
}

onMounted(()  => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))

interface ShortcutEntry {
  key:  string
  desc: string
}

interface ShortcutGroup {
  label:    string
  rows:     ShortcutEntry[]
}

const groups: ShortcutGroup[] = [
  {
    label: __('Timer'),
    rows: [
      { key: 'T',   desc: __('Start / Pause / Resume timer') },
      { key: 'S',   desc: __('Stop timer') },
    ],
  },
  {
    label: __('Entries'),
    rows: [
      { key: 'N',   desc: __('New entry (focus quick-add bar)') },
    ],
  },
  {
    label: __('Navigate'),
    rows: [
      { key: 'D',   desc: __('Today') },
      { key: 'W',   desc: __('This week') },
      { key: 'B',   desc: __('Prepare summary') },
      { key: '← →', desc: __('Previous / next day or week') },
    ],
  },
  {
    label: __('Help'),
    rows: [
      { key: 'H',   desc: __('Show / hide this overlay') },
      { key: 'Esc', desc: __('Close') },
    ],
  },
]
</script>

<template>
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    data-dialog-open="true"
    @click.self="emit('close')"
  >
    <!-- Panel -->
    <div
      class="relative w-full max-w-md rounded-2xl bg-[var(--watch-bg)] border border-[var(--watch-border)]
             shadow-2xl p-6"
      role="dialog"
      :aria-label="__('Keyboard Shortcuts')"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-5">
        <h2 class="text-base font-semibold text-[var(--watch-text)]">
          {{ __('Keyboard Shortcuts') }}
        </h2>
        <button
          type="button"
          class="p-1 rounded-lg text-[var(--watch-text-muted)] hover:text-[var(--watch-text)]
                 hover:bg-[var(--watch-bg-secondary)] transition-colors"
          :aria-label="__('Close')"
          @click="emit('close')"
        >
          <X class="w-4 h-4" aria-hidden="true" />
        </button>
      </div>

      <!-- Shortcut groups -->
      <div class="space-y-4 text-sm">
        <div v-for="group in groups" :key="group.label">
          <p class="text-xs font-semibold uppercase tracking-wide text-[var(--watch-text-muted)] mb-2">
            {{ group.label }}
          </p>
          <div class="space-y-1.5">
            <div v-for="row in group.rows" :key="row.key" class="flex items-center gap-3">
              <kbd class="inline-flex items-center justify-center min-w-[2.25rem] px-1.5 py-0.5
                          rounded border border-[var(--watch-border)] bg-[var(--watch-bg-secondary)]
                          text-xs font-mono font-medium text-[var(--watch-text)] shrink-0">
                {{ row.key }}
              </kbd>
              <span class="text-[var(--watch-text-secondary)]">{{ row.desc }}</span>
            </div>
          </div>
        </div>
      </div>

      <p class="mt-5 text-xs text-center text-[var(--watch-text-muted)]">
        {{ __('Press H or Esc to close') }}
      </p>
    </div>
  </div>
</template>
