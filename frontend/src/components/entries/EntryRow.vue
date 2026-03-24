<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { Clock, Lock, MoreHorizontal, Pencil, Copy, Calendar, CalendarDays, Trash2 } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { formatHours } from '@/composables/useEntries'
import type { TimeEntry, TagMeta, UpdateParams } from '@/composables/useEntries'
import EntryForm from './EntryForm.vue'

// ── Props / emits ────────────────────────────────────────────────────────

const props = defineProps<{
  entry: TimeEntry
  isToday?: boolean
}>()

const emit = defineEmits<{
  save:        [name: string, params: UpdateParams]
  duplicate:   [name: string]
  copyToToday: [name: string]
  copyToDate:  [name: string, date: string]
  delete:      [name: string]
  refresh:     []
}>()

// ── State ────────────────────────────────────────────────────────────────

const editing    = ref(false)
const menuOpen   = ref(false)
const confirming = ref(false)

// ── Menu ─────────────────────────────────────────────────────────────────

function closeMenu() {
  menuOpen.value  = false
  confirming.value = false
}

function toggleMenu(e: Event) {
  e.stopPropagation()
  if (!menuOpen.value) {
    menuOpen.value = true
    setTimeout(() => window.addEventListener('click', closeMenu, { once: true }), 0)
  } else {
    closeMenu()
  }
}

onUnmounted(() => window.removeEventListener('click', closeMenu))

function handleEdit() {
  closeMenu()
  editing.value = true
}

function handleDuplicate() {
  closeMenu()
  emit('duplicate', props.entry.name)
}

function handleCopyToToday() {
  closeMenu()
  emit('copyToToday', props.entry.name)
}

const copyDatePickerRef = ref<HTMLInputElement | null>(null)

function handleCopyToDate() {
  closeMenu()
  const el = copyDatePickerRef.value
  if (!el) return
  el.value = ''
  if (typeof el.showPicker === 'function') {
    el.showPicker()
  } else {
    el.click()
  }
}

function onCopyDateChange(e: Event) {
  const val = (e.target as HTMLInputElement).value
  if (val) emit('copyToDate', props.entry.name, val)
}

function handleDelete() {
  if (!confirming.value) {
    confirming.value = true
    return
  }
  closeMenu()
  emit('delete', props.entry.name)
}

// ── Row click to open edit ────────────────────────────────────────────────

function handleRowClick() {
  if (props.entry.entry_status === 'sent' || props.entry.is_running) return
  editing.value = true
}

// ── Save ─────────────────────────────────────────────────────────────────

function handleSave(params: UpdateParams) {
  editing.value = false
  emit('save', props.entry.name, params)
}

// ── Helpers ──────────────────────────────────────────────────────────────

function formatTime(t: string | null): string {
  if (!t) return ''
  return t.slice(0, 5)
}

const MAX_CHIPS = 3

const visibleTags = computed<TagMeta[]>(() => {
  const meta = props.entry.tag_meta ?? []
  return meta.slice(0, MAX_CHIPS)
})

const overflowCount = computed(() => {
  return Math.max(0, (props.entry.tag_meta?.length ?? 0) - MAX_CHIPS)
})

function chipStyle(tag: TagMeta) {
  const color = tag.color || 'var(--app-accent-500)'
  return {
    backgroundColor: `${color}22`,
    color,
    borderColor: `${color}44`,
  }
}

const BADGE_CLASS: Record<string, string> = {
  billable:       'badge-billable',
  'non-billable': 'badge-non-billable',
  internal:       'badge-internal',
}

const isSent    = computed(() => props.entry.entry_status === 'sent')
const isRunning = computed(() => !!props.entry.is_running)
const isLocked  = computed(() => isSent.value || isRunning.value)
</script>

<template>
  <!-- ── Edit mode ─────────────────────────────────────────────────── -->
  <div
    v-if="editing"
    class="bg-white dark:bg-slate-950 rounded-xl border border-[var(--app-accent-500)]/40 p-4"
  >
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('Edit Entry') }}</span>
    </div>
    <EntryForm
      :entry="entry"
      :default-date="entry.date"
      @save="handleSave"
      @cancel="editing = false"
      @refresh="editing = false; emit('refresh')"
    />
  </div>

  <!-- ── View mode ─────────────────────────────────────────────────── -->
  <div
    v-else
    class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 px-4 py-3
           transition-colors select-none"
    :class="[
      isLocked
        ? 'opacity-70 cursor-default'
        : 'cursor-pointer hover:border-[var(--app-accent-500)]/40 hover:bg-gray-50 dark:hover:bg-slate-800',
    ]"
    @click="handleRowClick"
  >
    <!-- Running indicator -->
    <div v-if="isRunning" class="flex items-center gap-1.5 mb-2">
      <span class="inline-block w-2 h-2 rounded-full bg-[var(--timer-running)] animate-pulse" />
      <span class="text-xs text-gray-500 dark:text-slate-500">{{ __('Timer running') }}</span>
    </div>

    <div class="flex items-start gap-3">

      <!-- Left: time + description + tags -->
      <div class="flex-1 min-w-0">
        <!-- Time range / duration -->
        <div class="flex items-center gap-2 mb-1">
          <Clock class="w-3.5 h-3.5 shrink-0 text-gray-500 dark:text-slate-500" aria-hidden="true" />
          <span class="text-xs text-gray-500 dark:text-slate-500 tabular-nums">
            <template v-if="entry.start_time && entry.end_time">
              {{ formatTime(entry.start_time) }} – {{ formatTime(entry.end_time) }}
            </template>
            <template v-else>
              {{ formatHours(entry.duration_hours) }}
            </template>
          </span>
          <span
            v-if="entry.start_time && entry.end_time"
            class="text-xs text-gray-500 dark:text-slate-500"
          >
            ({{ formatHours(entry.duration_hours) }})
          </span>
        </div>

        <!-- Description -->
        <p
          v-if="entry.description"
          class="text-sm text-gray-900 dark:text-slate-100 truncate mb-1.5"
        >
          {{ entry.description }}
        </p>
        <p
          v-else
          class="text-sm text-gray-500 dark:text-slate-500 italic mb-1.5"
        >
          {{ __('No description') }}
        </p>

        <!-- Tag chips (max 3 + overflow) -->
        <div
          v-if="entry.tag_meta?.length"
          class="flex flex-wrap gap-1"
          @click.stop
        >
          <span
            v-for="tag in visibleTags"
            :key="tag.name"
            class="px-1.5 py-0.5 rounded border text-xs font-medium"
            :style="chipStyle(tag)"
          >
            {{ tag.tag_name }}
          </span>
          <span
            v-if="overflowCount > 0"
            class="px-1.5 py-0.5 rounded text-xs text-gray-500 dark:text-slate-500
                   bg-gray-50 dark:bg-slate-800"
          >
            +{{ overflowCount }}
          </span>
        </div>
      </div>

      <!-- Right: badge + amount + lock / menu -->
      <div class="flex flex-col items-end gap-2 shrink-0">
        <span :class="['px-2 py-0.5 rounded text-xs font-medium', BADGE_CLASS[entry.entry_type]]">
          {{ __(entry.entry_type === 'billable'
            ? 'Billable'
            : entry.entry_type === 'non-billable'
            ? 'Non-billable'
            : 'Internal') }}
        </span>

        <!-- Lock icon for sent entries -->
        <Lock
          v-if="isSent"
          class="w-3.5 h-3.5 text-gray-500 dark:text-slate-500"
          aria-label="Sent — read only"
        />

        <!-- ⋯ menu (not for sent/running) -->
        <div v-else-if="!isRunning" class="relative" @click.stop>
          <button
            type="button"
            class="p-1.5 rounded hover:bg-gray-50 dark:hover:bg-slate-800
                   text-gray-500 dark:text-slate-500 hover:text-gray-900 dark:hover:text-slate-100 transition-colors"
            :title="__('More actions')"
            @click="toggleMenu"
          >
            <MoreHorizontal class="w-4 h-4" aria-hidden="true" />
          </button>

          <Transition
            enter-active-class="transition duration-100 ease-out"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="transition duration-75 ease-in"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div
              v-if="menuOpen"
              class="absolute right-0 top-full mt-1 w-40 rounded-lg border border-gray-200 dark:border-slate-700
                     bg-white dark:bg-slate-950 shadow-lg z-20 py-1"
              @click.stop
            >
              <button
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="handleEdit"
              >
                <Pencil class="w-4 h-4" aria-hidden="true" />
                {{ __('Edit') }}
              </button>
              <button
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="handleDuplicate"
              >
                <Copy class="w-4 h-4" aria-hidden="true" />
                {{ __('Duplicate') }}
              </button>
              <button
                v-if="!isToday"
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="handleCopyToToday"
              >
                <Calendar class="w-4 h-4" aria-hidden="true" />
                {{ __('Copy to today') }}
              </button>
              <button
                type="button"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="handleCopyToDate"
              >
                <CalendarDays class="w-4 h-4" aria-hidden="true" />
                {{ __('Copy to date…') }}
              </button>
              <button
                type="button"
                :class="[
                  'w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors',
                  confirming
                    ? 'bg-red-500 text-white hover:bg-red-600'
                    : 'text-red-500 hover:bg-gray-50 dark:hover:bg-slate-800',
                ]"
                @click="handleDelete"
              >
                <Trash2 class="w-4 h-4" aria-hidden="true" />
                {{ confirming ? __('Confirm delete') : __('Delete') }}
              </button>
            </div>
          </Transition>

          <!-- Hidden date input for "Copy to date…" -->
          <input
            ref="copyDatePickerRef"
            type="date"
            class="absolute opacity-0 pointer-events-none w-0 h-0"
            tabindex="-1"
            aria-hidden="true"
            @change="onCopyDateChange"
          />
        </div>
      </div>
    </div>

    <!-- Sent notice -->
    <p
      v-if="isSent"
      class="mt-2 text-xs text-gray-500 dark:text-slate-500 italic"
    >
      {{ __('This entry has been forwarded and cannot be edited.') }}
    </p>
  </div>
</template>
