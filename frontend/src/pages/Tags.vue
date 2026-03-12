<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Plus, X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import TagRow from '@/components/tags/TagRow.vue'
import type { TagData, TagSaveParams, BudgetStatus } from '@/components/tags/TagRow.vue'

// ── API helper ────────────────────────────────────────────────────────────

async function call<T = any>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  const res = await fetch(`/api/method/${method}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
    body: JSON.stringify(params),
  })
  const data = await res.json()
  if (!res.ok || data.exc) {
    let msg = 'Request failed'
    try { msg = JSON.parse(data._server_messages ?? '[]')[0]?.message ?? data.exc ?? msg } catch { /* ignore */ }
    throw new Error(msg)
  }
  return data.message as T
}

// ── State ─────────────────────────────────────────────────────────────────

const tags       = ref<TagData[]>([])
const budgets    = ref<Record<string, BudgetStatus>>({})
const loading    = ref(false)
const apiError   = ref<string | null>(null)
const filter     = ref('All')
const selected   = ref<Set<string>>(new Set())

// New-tag form
const showNewForm    = ref(false)
const newName        = ref('')
const newCategory    = ref('')
const newColor       = ref('')
const newType        = ref('')
const newRate        = ref<number | ''>('')
const newFormSaving  = ref(false)

// Merge dialog
const mergeSource   = ref<string | null>(null)
const mergeTarget   = ref('')
const mergeLoading  = ref(false)
const mergeError    = ref<string | null>(null)

// Bulk action states
const bulkChangeCat = ref(false)
const bulkNewCat    = ref('')

// ── Load ──────────────────────────────────────────────────────────────────

async function loadBudgets() {
  try {
    budgets.value = await call<Record<string, BudgetStatus>>('watch.api.tags.get_all_budgets')
  } catch { /* non-critical */ }
}

async function loadTags() {
  loading.value  = true
  apiError.value = null
  try {
    tags.value = await call<TagData[]>('watch.api.tag.get_tags', {
      include_archived: true,
      include_stats: true,
    })
    await loadBudgets()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(loadTags)

// ── Filter ────────────────────────────────────────────────────────────────

const FILTER_OPTIONS = ['All', 'Client', 'Project', 'Task', 'Category', 'Other', 'Archived']

const filteredTags = computed(() => {
  if (filter.value === 'All')      return tags.value.filter(t => !t.is_archived)
  if (filter.value === 'Archived') return tags.value.filter(t => t.is_archived)
  return tags.value.filter(t => t.category === filter.value && !t.is_archived)
})

// ── Selection ─────────────────────────────────────────────────────────────

function toggleSelect(tagName: string) {
  const s = new Set(selected.value)
  if (s.has(tagName)) s.delete(tagName)
  else s.add(tagName)
  selected.value = s
}

function clearSelection() {
  selected.value = new Set()
}

const selectedList = computed(() =>
  filteredTags.value.filter(t => selected.value.has(t.name))
)

// ── CRUD ──────────────────────────────────────────────────────────────────

async function handleCreate() {
  if (!newName.value.trim()) return
  newFormSaving.value = true
  apiError.value = null
  try {
    const tag = await call<TagData>('watch.api.tag.create_tag', {
      tag_name:             newName.value.trim(),
      category:             newCategory.value || null,
      color:                newColor.value || null,
      default_entry_type: newType.value || null,
      default_entry_rate: newRate.value !== '' ? Number(newRate.value) : null,
    })
    tags.value = [tag, ...tags.value]
    showNewForm.value = false
    newName.value = ''; newCategory.value = ''; newColor.value = ''
    newType.value = ''; newRate.value = ''
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    newFormSaving.value = false
  }
}

async function handleSave(tagName: string, params: TagSaveParams) {
  apiError.value = null
  try {
    let result: TagData
    if (params.tag_name !== tagName) {
      // Name changed → rename first
      result = await call<TagData>('watch.api.tag.rename_tag', {
        tag_name: tagName,
        new_name: params.tag_name,
      })
    } else {
      result = tagName as any // will be overwritten below
    }

    // Update other fields
    result = await call<TagData>('watch.api.tag.update_tag', {
      tag_name:                 params.tag_name,
      category:                 params.category || null,
      color:                    params.color || null,
      default_entry_type:       params.default_entry_type || null,
      default_entry_rate:       params.default_entry_rate !== '' ? Number(params.default_entry_rate) : null,
      monthly_hour_budget:      params.monthly_hour_budget !== '' ? Number(params.monthly_hour_budget) : 0,
      budget_warning_threshold: params.budget_warning_threshold !== '' ? Number(params.budget_warning_threshold) : 0,
    })

    const idx = tags.value.findIndex(t => t.name === tagName)
    if (idx !== -1) tags.value[idx] = { ...tags.value[idx], ...result }
    await loadBudgets()
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleArchive(tagName: string, archive: boolean) {
  apiError.value = null
  try {
    const result = await call<TagData>('watch.api.tag.archive_tag', { tag_name: tagName, archive })
    const idx = tags.value.findIndex(t => t.name === tagName)
    if (idx !== -1) tags.value[idx] = { ...tags.value[idx], ...result }
  } catch (e: any) {
    apiError.value = e.message
  }
}

async function handleDelete(tagName: string) {
  apiError.value = null
  try {
    await call('watch.api.tag.delete_tag', { tag_name: tagName })
    tags.value = tags.value.filter(t => t.name !== tagName)
    selected.value.delete(tagName)
  } catch (e: any) {
    apiError.value = e.message
  }
}

// ── Merge ─────────────────────────────────────────────────────────────────

function openMerge(tagName: string) {
  mergeSource.value  = tagName
  mergeTarget.value  = ''
  mergeError.value   = null
}

async function handleMerge() {
  if (!mergeSource.value || !mergeTarget.value) return
  mergeLoading.value = true
  mergeError.value   = null
  try {
    await call('watch.api.tag.merge_tag', {
      source: mergeSource.value,
      target: mergeTarget.value,
    })
    await loadTags()
    mergeSource.value = null
    mergeTarget.value = ''
  } catch (e: any) {
    mergeError.value = e.message
  } finally {
    mergeLoading.value = false
  }
}

// ── Bulk operations ───────────────────────────────────────────────────────

async function bulkArchive(archive: boolean) {
  apiError.value = null
  for (const tagName of selected.value) {
    await handleArchive(tagName, archive)
  }
  clearSelection()
}

async function bulkDelete() {
  apiError.value = null
  for (const tagName of [...selected.value]) {
    await handleDelete(tagName)
  }
  clearSelection()
}

async function bulkChangeCategory() {
  apiError.value = null
  for (const tagName of selected.value) {
    try {
      const result = await call<TagData>('watch.api.tag.update_tag', {
        tag_name: tagName,
        category: bulkNewCat.value,
      })
      const idx = tags.value.findIndex(t => t.name === tagName)
      if (idx !== -1) tags.value[idx] = { ...tags.value[idx], ...result }
    } catch (e: any) {
      apiError.value = e.message
      break
    }
  }
  bulkChangeCat.value = false
  bulkNewCat.value    = ''
  clearSelection()
}

const CATEGORIES = ['', 'Client', 'Project', 'Task', 'Category', 'Other']
const BILLING_TYPES = [
  { value: '', label: '—' },
  { value: 'billable', label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal', label: 'Internal' },
]

// Merge target options (all tags except source)
const mergeTargetOptions = computed(() =>
  tags.value.filter(t => t.name !== mergeSource.value && !t.is_archived)
)
</script>

<template>
  <div class="min-h-screen bg-[var(--watch-bg-secondary)]">
    <div class="max-w-3xl mx-auto px-4 py-6 space-y-4">

      <!-- Header -->
      <div class="flex items-center justify-between">
        <h1 class="text-lg font-semibold text-[var(--watch-text)]">{{ __('Tags') }}</h1>
        <div class="flex items-center gap-2">
          <!-- Category filter -->
          <select
            v-model="filter"
            class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                   focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
          >
            <option v-for="f in FILTER_OPTIONS" :key="f" :value="f">{{ __(f) }}</option>
          </select>

          <button
            type="button"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--watch-primary)]
                   hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium transition-colors"
            @click="showNewForm = !showNewForm"
          >
            <Plus class="w-4 h-4" aria-hidden="true" />
            {{ __('New Tag') }}
          </button>
        </div>
      </div>

      <!-- New tag form -->
      <div
        v-if="showNewForm"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-primary)]/40 p-4 space-y-3"
      >
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[var(--watch-text-muted)]">{{ __('Name') }}</label>
            <input
              v-model="newName"
              type="text"
              :placeholder="__('Tag name')"
              class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                     bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                     focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
              @keydown.enter="handleCreate"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[var(--watch-text-muted)]">{{ __('Category') }}</label>
            <select
              v-model="newCategory"
              class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                     bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                     focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
            >
              <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c || __('— none —') }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[var(--watch-text-muted)]">{{ __('Color') }}</label>
            <input v-model="newColor" type="color" class="w-8 h-8 rounded cursor-pointer border border-[var(--watch-border)]" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[var(--watch-text-muted)]">{{ __('Default Type') }}</label>
            <select
              v-model="newType"
              class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                     bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                     focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
            >
              <option v-for="bt in BILLING_TYPES" :key="bt.value" :value="bt.value">{{ __(bt.label) }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1 col-span-2">
            <label class="text-xs text-[var(--watch-text-muted)]">{{ __('Default Rate / h') }}</label>
            <input v-model="newRate" type="number" min="0" step="0.01" placeholder="0.00"
              class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                     bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                     focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]" />
          </div>
        </div>
        <div class="flex gap-2">
          <button
            type="button"
            class="flex-1 py-2 rounded-lg border border-[var(--watch-border)]
                   text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)] transition-colors"
            @click="showNewForm = false"
          >{{ __('Cancel') }}</button>
          <button
            type="button"
            class="flex-1 py-2 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                   text-white text-sm font-medium transition-colors disabled:opacity-50"
            :disabled="!newName.trim() || newFormSaving"
            @click="handleCreate"
          >{{ __('Create Tag') }}</button>
        </div>
      </div>

      <!-- API error -->
      <p v-if="apiError" class="text-sm text-red-500 px-1">{{ apiError }}</p>

      <!-- Bulk action bar -->
      <div
        v-if="selected.size > 0"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] px-4 py-2
               flex items-center gap-3 flex-wrap"
      >
        <span class="text-sm font-medium text-[var(--watch-text)]">
          {{ selected.size }} {{ __('selected') }}
        </span>

        <div v-if="!bulkChangeCat" class="flex items-center gap-2 ml-auto flex-wrap">
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                   text-xs text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)] transition-colors"
            @click="bulkArchive(true)"
          >{{ __('Archive') }}</button>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                   text-xs text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)] transition-colors"
            @click="bulkArchive(false)"
          >{{ __('Unarchive') }}</button>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                   text-xs text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)] transition-colors"
            @click="bulkChangeCat = true"
          >{{ __('Change Category') }}</button>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg border border-red-300
                   text-xs text-red-500 hover:bg-red-50 transition-colors"
            @click="bulkDelete"
          >{{ __('Delete') }}</button>
          <button
            type="button"
            class="p-1 text-[var(--watch-text-muted)] hover:text-[var(--watch-text)] transition-colors"
            @click="clearSelection"
          >
            <X class="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <!-- Bulk change category inline -->
        <div v-if="bulkChangeCat" class="flex items-center gap-2 ml-auto">
          <select
            v-model="bulkNewCat"
            class="px-2 py-1.5 rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none"
          >
            <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c || __('— none —') }}</option>
          </select>
          <button
            type="button"
            class="px-3 py-1.5 rounded-lg bg-[var(--watch-primary)] text-white text-xs font-medium
                   hover:bg-[var(--watch-primary-dark)] transition-colors"
            @click="bulkChangeCategory"
          >{{ __('Apply') }}</button>
          <button type="button" class="text-xs text-[var(--watch-text-muted)]" @click="bulkChangeCat = false">
            {{ __('Cancel') }}
          </button>
        </div>
      </div>

      <!-- Column header -->
      <div
        v-if="!loading && filteredTags.length"
        class="flex items-center gap-3 px-4 text-xs text-[var(--watch-text-muted)]"
      >
        <span class="w-4 shrink-0" />
        <span class="w-2.5 shrink-0" />
        <span class="flex-1">{{ __('Name') }}</span>
        <span class="w-20 shrink-0">{{ __('Category') }}</span>
        <span class="w-20 shrink-0 text-right">{{ __('Rate') }}</span>
        <span class="w-24 shrink-0 text-right">{{ __('Type') }}</span>
        <span class="w-16 shrink-0 text-right">{{ __('Entries') }}</span>
        <span class="w-8 shrink-0" />
      </div>

      <!-- Loading skeleton -->
      <template v-if="loading">
        <div
          v-for="i in 5"
          :key="i"
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-4 animate-pulse"
        >
          <div class="h-4 bg-[var(--watch-border)] rounded w-1/3" />
        </div>
      </template>

      <!-- Empty state -->
      <div
        v-else-if="!filteredTags.length"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-6 text-center"
      >
        <p class="text-sm text-[var(--watch-text-muted)]">
          {{ filter === 'All' ? __('No tags yet. Create your first tag.') : __('No tags in this category.') }}
        </p>
      </div>

      <!-- Tag rows -->
      <TagRow
        v-for="tag in filteredTags"
        :key="tag.name"
        :tag="tag"
        :is-selected="selected.has(tag.name)"
        :budget-status="budgets[tag.name] ?? null"
        @toggle-select="toggleSelect(tag.name)"
        @save="(params) => handleSave(tag.name, params)"
        @archive="(archive) => handleArchive(tag.name, archive)"
        @delete="handleDelete(tag.name)"
        @merge="openMerge(tag.name)"
      />

    </div>
  </div>

  <!-- ── Merge confirmation dialog ──────────────────────────────────── -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="mergeSource"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="mergeSource = null"
      >
        <div class="bg-[var(--watch-bg)] rounded-2xl border border-[var(--watch-border)] p-6 w-full max-w-md shadow-xl">
          <h2 class="text-base font-semibold text-[var(--watch-text)] mb-1">
            {{ __('Merge tag') }}
          </h2>
          <p class="text-sm text-[var(--watch-text-secondary)] mb-4">
            {{ __('All entries tagged') }}
            <strong>{{ mergeSource }}</strong>
            {{ __('will be re-tagged with the target. The source will be archived. This cannot be undone.') }}
          </p>

          <label class="text-xs text-[var(--watch-text-muted)] block mb-1">{{ __('Merge into') }}</label>
          <select
            v-model="mergeTarget"
            class="w-full px-3 py-2 mb-4 rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none
                   focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
          >
            <option value="">{{ __('— select target —') }}</option>
            <option v-for="t in mergeTargetOptions" :key="t.name" :value="t.name">
              {{ t.tag_name }}
            </option>
          </select>

          <p v-if="mergeError" class="text-xs text-red-500 mb-3">{{ mergeError }}</p>

          <div class="flex gap-2">
            <button
              type="button"
              class="flex-1 py-2 rounded-lg border border-[var(--watch-border)]
                     text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)] transition-colors"
              @click="mergeSource = null"
            >{{ __('Cancel') }}</button>
            <button
              type="button"
              class="flex-1 py-2 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                     text-white text-sm font-medium transition-colors disabled:opacity-50"
              :disabled="!mergeTarget || mergeLoading"
              @click="handleMerge"
            >{{ __('Merge & Archive') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
