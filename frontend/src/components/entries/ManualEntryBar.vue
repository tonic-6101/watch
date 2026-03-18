<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { parseDurationInput } from '@/composables/useEntries'
import type { CreateParams } from '@/composables/useEntries'
import type { EntryType } from '@/composables/useTimer'
import EntryForm from './EntryForm.vue'
import TagInput from '@/components/timer/TagInput.vue'

// ── Props / emits ────────────────────────────────────────────────────────

const props = defineProps<{
  date: string
}>()

const emit = defineEmits<{
  /** Parent calls create() with these params, then refreshes the list. */
  save: [params: CreateParams]
}>()

// ── State ────────────────────────────────────────────────────────────────

const expanded    = ref(false)
const descInputRef = ref<HTMLInputElement | null>(null)

defineExpose({
  focus() {
    expanded.value = false
    nextTick(() => descInputRef.value?.focus())
  },
})

// Quick-bar fields
const quickDesc     = ref('')
const quickDuration = ref('')
const quickTags     = ref<string[]>([])
const quickType     = ref<EntryType>('billable')

// ── Actions ──────────────────────────────────────────────────────────────

function handleQuickSave() {
  const hours = parseDurationInput(quickDuration.value)
  if (!hours) return
  emit('save', {
    date:           props.date,
    duration_hours: hours,
    description:    quickDesc.value || null,
    entry_type:   quickType.value,
    tags:           quickTags.value,
  })
  quickDesc.value     = ''
  quickDuration.value = ''
  quickTags.value     = []
  quickType.value     = 'billable'
}

function handleFormSave(params: CreateParams) {
  expanded.value = false
  emit('save', params)
}

const ENTRY_OPTIONS: { value: EntryType; label: string }[] = [
  { value: 'billable',     label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal',     label: 'Internal' },
]
</script>

<template>
  <div class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-3">

    <!-- ── Quick bar ──────────────────────────────────────────────── -->
    <div v-if="!expanded" class="space-y-2">

      <!-- Row 1: Description + Duration + Save -->
      <div class="flex items-center gap-2">
        <input
          ref="descInputRef"
          v-model="quickDesc"
          type="text"
          :placeholder="__('What did you work on?')"
          class="flex-1 min-w-0 px-3 py-2 rounded-lg border border-[var(--watch-border)]
                 bg-[var(--watch-bg)] text-sm text-[var(--watch-text)]
                 placeholder-[var(--watch-text-muted)] outline-none
                 focus:ring-2 focus:ring-[var(--watch-primary)]/30
                 focus:border-[var(--watch-primary)]"
          @keydown.enter.prevent="handleQuickSave"
        />
        <input
          v-model="quickDuration"
          type="text"
          placeholder="h:mm"
          class="w-16 shrink-0 px-2 py-2 rounded-lg border border-[var(--watch-border)]
                 bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] text-center outline-none
                 focus:ring-2 focus:ring-[var(--watch-primary)]/30
                 focus:border-[var(--watch-primary)]"
          @keydown.enter.prevent="handleQuickSave"
        />
        <button
          type="button"
          class="shrink-0 px-3 py-2 rounded-lg bg-[var(--watch-primary)]
                 hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium
                 transition-colors disabled:opacity-50"
          :disabled="!parseDurationInput(quickDuration)"
          @click="handleQuickSave"
        >
          {{ __('Save') }}
        </button>
      </div>

      <!-- Row 2: Tags + Billing type + More -->
      <div class="flex items-center gap-2 flex-wrap">
        <div class="flex-1 min-w-[140px]">
          <TagInput v-model="quickTags" />
        </div>
        <div class="flex gap-1 shrink-0">
          <button
            v-for="opt in ENTRY_OPTIONS"
            :key="opt.value"
            type="button"
            :class="[
              'px-2 py-1 rounded text-xs font-medium border transition-colors',
              quickType === opt.value
                ? 'bg-[var(--watch-primary)] border-[var(--watch-primary)] text-white'
                : 'border-[var(--watch-border)] text-[var(--watch-text-secondary)] hover:border-[var(--watch-primary)]/50',
            ]"
            @click="quickType = opt.value"
          >
            {{ __(opt.label) }}
          </button>
        </div>

        <button
          type="button"
          class="ml-auto flex items-center gap-1 text-xs text-[var(--watch-text-muted)]
                 hover:text-[var(--watch-text)] transition-colors"
          @click="expanded = true"
        >
          {{ __('More') }}
          <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- ── Expanded full form ────────────────────────────────────── -->
    <div v-else>
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm font-semibold text-[var(--watch-text)]">
          {{ __('Add Entry') }}
        </span>
        <button
          type="button"
          class="flex items-center gap-1 text-xs text-[var(--watch-text-muted)]
                 hover:text-[var(--watch-text)] transition-colors"
          @click="expanded = false"
        >
          {{ __('Less') }}
          <ChevronUp class="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      </div>

      <EntryForm
        :default-date="date"
        @save="handleFormSave"
        @cancel="expanded = false"
      />
    </div>

  </div>
</template>
