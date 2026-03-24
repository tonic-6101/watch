<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { MoreHorizontal, Pencil, Archive, ArchiveRestore, Trash2, GitMerge } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { formatHours } from '@/composables/useEntries'
import type { EntryType } from '@/composables/useTimer'

// ── Types ────────────────────────────────────────────────────────────────

export interface TagData {
  name: string
  tag_name: string
  category: string
  color: string | null
  default_entry_type: EntryType | null
  is_archived: number
  monthly_hour_budget?: number | null
  budget_warning_threshold?: number | null
  entry_count?: number
  last_used?: string | null
}

export interface BudgetStatus {
  used: number
  budget: number
  pct: number | null
  status: 'none' | 'approaching' | 'exceeded'
  threshold_pct: number
}

export interface TagSaveParams {
  tag_name: string
  category: string
  color: string
  default_entry_type: string
  monthly_hour_budget: number | ''
  budget_warning_threshold: number | ''
}

// ── Props / emits ────────────────────────────────────────────────────────

const props = defineProps<{
  tag: TagData
  isSelected: boolean
  budgetStatus?: BudgetStatus | null
}>()

const emit = defineEmits<{
  toggleSelect: []
  edit:         []
  cancelEdit:   []
  save:         [params: TagSaveParams]
  archive:      [archive: boolean]
  delete:       []
  merge:        []
}>()

// ── Edit form state ──────────────────────────────────────────────────────

const editing = ref(false)
const editName      = ref(props.tag.tag_name)
const editCategory  = ref(props.tag.category ?? '')
const editColor     = ref(props.tag.color ?? '')
const editType      = ref(props.tag.default_entry_type ?? '')
const editBudget    = ref<number | ''>(props.tag.monthly_hour_budget || '')
const editThreshold = ref<number | ''>(props.tag.budget_warning_threshold || '')

function openEdit() {
  editName.value      = props.tag.tag_name
  editCategory.value  = props.tag.category ?? ''
  editColor.value     = props.tag.color ?? ''
  editType.value      = props.tag.default_entry_type ?? ''
  editBudget.value    = props.tag.monthly_hour_budget || ''
  editThreshold.value = props.tag.budget_warning_threshold || ''
  editing.value       = true
  menuOpen.value      = false
}

function handleSave() {
  emit('save', {
    tag_name:               editName.value.trim(),
    category:               editCategory.value,
    color:                  editColor.value,
    default_entry_type:     editType.value,
    monthly_hour_budget:    editBudget.value,
    budget_warning_threshold: editThreshold.value,
  })
  editing.value = false
}

// ── Menu ─────────────────────────────────────────────────────────────────

const menuOpen      = ref(false)
const confirmDelete = ref(false)

function closeMenu() {
  menuOpen.value     = false
  confirmDelete.value = false
}

function toggleMenu() {
  if (!menuOpen.value) {
    menuOpen.value = true
    setTimeout(() => window.addEventListener('click', closeMenu, { once: true }), 0)
  } else {
    closeMenu()
  }
}

onUnmounted(() => window.removeEventListener('click', closeMenu))

function handleDelete() {
  menuOpen.value = false
  if (!confirmDelete.value) {
    confirmDelete.value = true
    return
  }
  confirmDelete.value = false
  emit('delete')
}

// ── Helpers ──────────────────────────────────────────────────────────────

const CATEGORIES = ['', 'Client', 'Project', 'Task', 'Category', 'Other']
const BILLING_TYPES = [
  { value: '', label: '—' },
  { value: 'billable', label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal', label: 'Internal' },
]

const dotStyle = computed(() => ({
  backgroundColor: props.tag.color || 'var(--app-accent-500)',
}))

const showBudgetBar = computed(() =>
  (props.tag.monthly_hour_budget ?? 0) > 0 && props.budgetStatus != null,
)

const budgetBarColor = computed(() => {
  if (!props.budgetStatus) return 'bg-[var(--app-accent-500)]'
  if (props.budgetStatus.status === 'exceeded') return 'bg-red-500'
  if (props.budgetStatus.status === 'approaching') return 'bg-amber-400'
  return 'bg-[var(--app-accent-500)]'
})

const budgetMonthLabel = computed(() => {
  const d = new Date()
  return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
})
</script>

<template>
  <!-- ── Edit mode ──────────────────────────────────────────────────── -->
  <div
    v-if="editing"
    class="bg-white dark:bg-slate-950 rounded-xl border border-[var(--app-accent-500)]/40 p-4 space-y-3"
  >
    <div class="grid grid-cols-2 gap-3">
      <!-- Name -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Name') }}</label>
        <input
          v-model="editName"
          type="text"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
        />
      </div>

      <!-- Category -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Category') }}</label>
        <select
          v-model="editCategory"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
        >
          <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c || __('— none —') }}</option>
        </select>
      </div>

      <!-- Color -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Color') }}</label>
        <div class="flex items-center gap-2">
          <input
            v-model="editColor"
            type="color"
            class="w-8 h-8 rounded cursor-pointer border border-gray-200 dark:border-slate-700"
          />
          <span class="text-xs text-gray-500 dark:text-slate-500">{{ editColor || '—' }}</span>
        </div>
      </div>

      <!-- Default billing type -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Default Type') }}</label>
        <select
          v-model="editType"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
        >
          <option v-for="bt in BILLING_TYPES" :key="bt.value" :value="bt.value">{{ __(bt.label) }}</option>
        </select>
      </div>

      <!-- Monthly budget -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Monthly Budget (h)') }}</label>
        <input
          v-model="editBudget"
          type="number"
          min="0"
          step="0.5"
          :placeholder="__('0 = no limit')"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
        />
      </div>

      <!-- Budget warning threshold -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Warn at (%)') }}</label>
        <input
          v-model="editThreshold"
          type="number"
          min="0"
          max="100"
          step="5"
          :placeholder="__('0 = site default')"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
        />
      </div>
    </div>

    <div class="flex gap-2">
      <button
        type="button"
        class="flex-1 py-2 rounded-lg border border-gray-200 dark:border-slate-700
               text-sm text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
        @click="editing = false; emit('cancelEdit')"
      >
        {{ __('Cancel') }}
      </button>
      <button
        type="button"
        class="flex-1 py-2 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
               text-white text-sm font-medium transition-colors disabled:opacity-50"
        :disabled="!editName.trim()"
        @click="handleSave"
      >
        {{ __('Save') }}
      </button>
    </div>
  </div>

  <!-- ── View mode ──────────────────────────────────────────────────── -->
  <div
    v-else
    class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
           transition-colors"
    :class="{ 'opacity-60': tag.is_archived }"
  >
  <div class="px-4 py-3 flex items-center gap-3">
    <!-- Checkbox -->
    <input
      type="checkbox"
      :checked="isSelected"
      class="rounded accent-[var(--app-accent-500)] cursor-pointer shrink-0"
      @change="emit('toggleSelect')"
    />

    <!-- Color dot -->
    <span
      class="inline-block w-2.5 h-2.5 rounded-full shrink-0"
      :style="dotStyle"
    />

    <!-- Name + archived badge -->
    <div class="flex-1 min-w-0">
      <span class="text-sm font-medium text-gray-900 dark:text-slate-100 truncate">
        {{ tag.tag_name }}
      </span>
      <span
        v-if="tag.is_archived"
        class="ml-2 px-1.5 py-0.5 rounded text-xs bg-gray-50 dark:bg-slate-800
               text-gray-500 dark:text-slate-500"
      >
        {{ __('archived') }}
      </span>
    </div>

    <!-- Category -->
    <span class="text-xs text-gray-500 dark:text-slate-500 w-20 shrink-0">
      {{ tag.category || '—' }}
    </span>

    <!-- Default billing type -->
    <span class="text-xs text-gray-500 dark:text-slate-500 w-24 shrink-0 text-right capitalize">
      {{ tag.default_entry_type || '—' }}
    </span>

    <!-- Entry count -->
    <span class="text-xs text-gray-500 dark:text-slate-500 w-16 shrink-0 text-right">
      {{ tag.entry_count ?? '—' }}
    </span>

    <!-- Actions menu -->
    <div class="relative shrink-0">
      <button
        type="button"
        class="p-1.5 rounded hover:bg-gray-50 dark:hover:bg-slate-800
               text-gray-500 dark:text-slate-500 hover:text-gray-900 dark:hover:text-slate-100 transition-colors"
        @click.stop="toggleMenu"
      >
        <MoreHorizontal class="w-4 h-4" aria-hidden="true" />
      </button>

      <!-- Dropdown -->
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
          class="absolute right-0 top-full mt-1 w-44 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 shadow-lg z-20 py-1"
          @click.stop
        >
          <button
            type="button"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                   hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            @click="openEdit"
          >
            <Pencil class="w-4 h-4" aria-hidden="true" />
            {{ __('Edit') }}
          </button>
          <button
            type="button"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                   hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            @click="closeMenu(); emit('merge')"
          >
            <GitMerge class="w-4 h-4" aria-hidden="true" />
            {{ __('Merge into…') }}
          </button>
          <button
            type="button"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-900 dark:text-slate-100
                   hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            @click="closeMenu(); emit('archive', !tag.is_archived)"
          >
            <component
              :is="tag.is_archived ? ArchiveRestore : Archive"
              class="w-4 h-4"
              aria-hidden="true"
            />
            {{ tag.is_archived ? __('Unarchive') : __('Archive') }}
          </button>
          <button
            v-if="!tag.entry_count"
            type="button"
            :class="[
              'w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors',
              confirmDelete
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'text-red-500 hover:bg-gray-50 dark:hover:bg-slate-800',
            ]"
            @click="handleDelete"
          >
            <Trash2 class="w-4 h-4" aria-hidden="true" />
            {{ confirmDelete ? __('Confirm delete') : __('Delete') }}
          </button>
        </div>
      </Transition>
    </div>
  </div>

  <!-- Budget progress bar -->
  <div
    v-if="showBudgetBar && budgetStatus"
    class="px-4 pb-3 pt-0"
  >
    <!-- Bar -->
    <div class="h-1.5 rounded-full bg-gray-50 dark:bg-slate-800 overflow-hidden mb-1">
      <div
        class="h-full rounded-full transition-all"
        :class="budgetBarColor"
        :style="{ width: `${Math.min(budgetStatus.pct ?? 0, 100)}%` }"
      />
    </div>
    <!-- Label row -->
    <div class="flex items-center gap-2 text-xs">
      <span class="text-gray-500 dark:text-slate-500">
        {{ formatHours(budgetStatus.used) }} / {{ formatHours(budgetStatus.budget) }}
        <template v-if="budgetStatus.pct != null"> ({{ budgetStatus.pct }}%)</template>
      </span>
      <span
        v-if="budgetStatus.status === 'approaching'"
        class="text-amber-500"
      >⚠ {{ __('Approaching limit') }}</span>
      <span
        v-else-if="budgetStatus.status === 'exceeded'"
        class="text-red-500"
      >🔴 {{ __('Budget exceeded') }}</span>
      <span class="ml-auto text-gray-500 dark:text-slate-500">{{ budgetMonthLabel }}</span>
    </div>
  </div>

  </div>
</template>
