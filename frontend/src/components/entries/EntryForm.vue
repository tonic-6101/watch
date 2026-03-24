<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { __ } from '@/composables/useTranslate'
import {
  formatHours,
  parseDurationInput,
  formatDurationInput,
  timeToMinutes,
  minutesToTime,
  daysAgo,
} from '@/composables/useEntries'
import type { TimeEntry, CreateParams, UpdateParams } from '@/composables/useEntries'
import type { EntryType } from '@/composables/useTimer'
import TagInput from '@/components/timer/TagInput.vue'

// ── Tag metadata cache ───────────────────────────────────────────────────

interface TagMeta {
  name: string
  category: string
  default_entry_type: EntryType | null
}

const tagMetaCache = new Map<string, TagMeta>()

async function fetchTagMeta(tagName: string): Promise<TagMeta | null> {
  if (tagMetaCache.has(tagName)) return tagMetaCache.get(tagName)!
  try {
    const res = await fetch(
      `/api/method/watch.api.tags.get_tags?search=${encodeURIComponent(tagName)}&include_archived=true`,
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    const tags: any[] = data.message ?? []
    const match = tags.find(t => t.tag_name === tagName || t.name === tagName)
    if (!match) return null
    const meta: TagMeta = {
      name: match.name,
      category: match.category ?? 'Other',
      default_entry_type: match.default_entry_type || null,
    }
    tagMetaCache.set(tagName, meta)
    return meta
  } catch {
    return null
  }
}

// ── Props / emits ────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  /** Existing entry to edit. Null = create mode. */
  entry?: TimeEntry | null
  /** Pre-filled date for new entries (daily view's current date). */
  defaultDate: string
  /** When true, hide the date picker (used inside ManualEntryBar). */
  hideDate?: boolean
}>(), {
  entry: null,
  hideDate: false,
})

const emit = defineEmits<{
  save:    [params: CreateParams | UpdateParams]
  cancel:  []
  refresh: []
}>()

// ── Form state ───────────────────────────────────────────────────────────

const formDate       = ref(props.entry?.date ?? props.defaultDate)
const formDesc       = ref(props.entry?.description ?? '')
const formTags       = ref<string[]>(props.entry?.tag_names ? [...props.entry.tag_names] : [])
const formType       = ref<EntryType>((props.entry?.entry_type ?? 'billable') as EntryType)
const formDuration   = ref(props.entry?.duration_hours ? formatDurationInput(props.entry.duration_hours) : '')
const formStart      = ref(props.entry?.start_time ? props.entry.start_time.slice(0, 5) : '')
const formEnd        = ref(props.entry?.end_time   ? props.entry.end_time.slice(0, 5)   : '')
const formLinearIssue = ref(props.entry?.linear_issue ?? '')
const formGithubRef   = ref(props.entry?.github_ref ?? '')
const saving         = ref(false)
const saveError      = ref<string | null>(null)

// ── Integration visibility (driven by Watch Settings) ───────────────────

const hasLinear = ref(false)
const hasGitHub = ref(false)
const integrationsOpen = ref(!!(props.entry?.linear_issue || props.entry?.github_ref))

// ── Integration autocomplete ────────────────────────────────────────────

interface AutocompleteItem { value: string; label: string; url?: string }

const linearSuggestions = ref<AutocompleteItem[]>([])
const githubSuggestions = ref<AutocompleteItem[]>([])
let linearDebounce: ReturnType<typeof setTimeout> | null = null
let githubDebounce: ReturnType<typeof setTimeout> | null = null

function searchLinear(query: string) {
  if (linearDebounce) clearTimeout(linearDebounce)
  if (query.length < 2) { linearSuggestions.value = []; return }
  linearDebounce = setTimeout(async () => {
    try {
      const res = await fetch(
        `/api/method/watch.api.integrations.search_linear_issues?query=${encodeURIComponent(query)}`,
        { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
      )
      const data = await res.json()
      linearSuggestions.value = data.message ?? []
    } catch { linearSuggestions.value = [] }
  }, 300)
}

function searchGitHub(query: string) {
  if (githubDebounce) clearTimeout(githubDebounce)
  if (query.length < 1) { githubSuggestions.value = []; return }
  githubDebounce = setTimeout(async () => {
    try {
      const res = await fetch(
        `/api/method/watch.api.integrations.search_github_issues?query=${encodeURIComponent(query)}`,
        { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
      )
      const data = await res.json()
      githubSuggestions.value = data.message ?? []
    } catch { githubSuggestions.value = [] }
  }, 300)
}

function selectLinear(item: AutocompleteItem) {
  formLinearIssue.value = item.value
  linearSuggestions.value = []
}

function selectGitHub(item: AutocompleteItem) {
  formGithubRef.value = item.value
  githubSuggestions.value = []
}

function dismissLinearSuggestions() {
  window.setTimeout(() => { linearSuggestions.value = [] }, 200)
}
function dismissGithubSuggestions() {
  window.setTimeout(() => { githubSuggestions.value = [] }, 200)
}

// ── Budget warning ───────────────────────────────────────────────────────

interface BudgetStatus {
  used: number; budget: number; pct: number | null
  status: 'none' | 'approaching' | 'exceeded'; threshold_pct: number
}

const budgetCache   = new Map<string, BudgetStatus>()
const budgetWarning = ref<{ tag: string; b: BudgetStatus } | null>(null)

async function checkTagBudgets(tags: string[]) {
  budgetWarning.value = null
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
  budgetWarning.value = worst
}

// ── Tag inheritance ──────────────────────────────────────────────────────
// 'default' = never touched  |  'inherited' = set by tag  |  'manual' = user chose

type InheritSource = 'default' | 'inherited' | 'manual'
const typeSource     = ref<InheritSource>(props.entry ? 'manual' : 'default')

// ── Site defaults from Watch Settings ───────────────────────────────────
// Applied once on mount for new entries, before any tag interaction.

onMounted(async () => {
  // Always check budget for pre-populated tags (edit mode)
  if (formTags.value.length) checkTagBudgets(formTags.value)

  try {
    const res = await fetch(
      '/api/method/frappe.client.get?doctype=Watch+Settings&name=Watch+Settings',
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    const settings = data.message ?? {}

    // Integration visibility
    hasLinear.value = !!settings.linear_api_key
    hasGitHub.value = !!settings.github_token

    if (props.entry) return   // edit mode — use existing values for defaults below

    if (typeSource.value === 'default' && settings.default_entry_type) {
      formType.value  = settings.default_entry_type as EntryType
    }
  } catch { /* silently ignore — site defaults are optional */ }
})

watch(formTags, async (newTags, oldTags) => {
  checkTagBudgets(newTags ?? [])

  // Only apply tag inheritance when a tag is added (list grew)
  if (!newTags || newTags.length <= (oldTags?.length ?? 0)) return
  const added = newTags[newTags.length - 1]
  const meta = await fetchTagMeta(added)
  if (!meta) return

  // entry_type: inherit from first Client tag, or any tag, if not manually set
  if (typeSource.value !== 'manual' && meta.default_entry_type) {
    if (meta.category === 'Client' || typeSource.value === 'default') {
      formType.value  = meta.default_entry_type
      typeSource.value = 'inherited'
    }
  }
}, { deep: true })

// ── Three-way sync: duration ↔ start ↔ end ──────────────────────────────
// Duration is the anchor. Editing start+end recalculates duration.
// Editing duration (when start exists) recalculates end.

let _syncLock = false

function syncFromDuration() {
  if (_syncLock) return
  const hours = parseDurationInput(formDuration.value)
  if (hours === null || !formStart.value) return
  _syncLock = true
  const startMin = timeToMinutes(formStart.value)
  if (startMin !== null) {
    formEnd.value = minutesToTime(startMin + Math.round(hours * 60))
  }
  _syncLock = false
}

function syncFromTimes() {
  if (_syncLock) return
  if (!formStart.value || !formEnd.value) return
  const startMin = timeToMinutes(formStart.value)
  const endMin   = timeToMinutes(formEnd.value)
  if (startMin === null || endMin === null) return
  const diffMin = endMin - startMin
  if (diffMin <= 0) return
  _syncLock = true
  formDuration.value = formatDurationInput(diffMin / 60)
  _syncLock = false
}

watch(formDuration, syncFromDuration)
watch(formStart, syncFromTimes)
watch(formEnd,   syncFromTimes)

// ── Validation ───────────────────────────────────────────────────────────

const durationHours = computed(() => parseDurationInput(formDuration.value))
const canSave       = computed(() => durationHours.value !== null && durationHours.value > 0)

const pastDaysCount = computed(() => daysAgo(formDate.value))
const showPastWarning = computed(() =>
  !props.hideDate && pastDaysCount.value > 7,
)

// ── Submit ───────────────────────────────────────────────────────────────

async function handleSave() {
  if (!canSave.value) return
  saving.value    = true
  saveError.value = null
  try {
    const params: CreateParams | UpdateParams = {
      date:           formDate.value,
      duration_hours: durationHours.value ?? undefined,
      start_time:     formStart.value || null,
      end_time:       formEnd.value   || null,
      description:    formDesc.value  || null,
      entry_type:   formType.value,
      tags:           formTags.value,
      linear_issue:   formLinearIssue.value || null,
      github_ref:     formGithubRef.value || null,
    }
    emit('save', params)
  } finally {
    saving.value = false
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────

const ENTRY_OPTIONS: { value: EntryType; label: string }[] = [
  { value: 'billable',     label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal',     label: 'Internal' },
]

// ── Time input helpers (24h format) ─────────────────────────────────────

/** Returns true for valid HH:MM (24h). */
function isValidTime(v: string): boolean {
  const m = v.match(/^(\d{1,2}):(\d{2})$/)
  if (!m) return false
  const h = parseInt(m[1]), min = parseInt(m[2])
  return h >= 0 && h <= 23 && min >= 0 && min <= 59
}

/** Normalize loose input like "9:5" → "09:05", or "930" → "09:30". */
function normalizeTimeInput(v: string): string {
  if (!v) return ''
  // Already valid HH:MM
  if (isValidTime(v)) {
    const [h, m] = v.split(':')
    return `${h.padStart(2, '0')}:${m}`
  }
  // Try digits-only: "930" → "09:30", "1430" → "14:30"
  const digits = v.replace(/\D/g, '')
  if (digits.length === 3 || digits.length === 4) {
    const hStr = digits.slice(0, digits.length - 2)
    const mStr = digits.slice(-2)
    const h = parseInt(hStr), m = parseInt(mStr)
    if (h >= 0 && h <= 23 && m >= 0 && m <= 59) {
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
    }
  }
  return v
}
</script>

<template>
  <div class="space-y-3">

    <!-- Description -->
    <input
      v-model="formDesc"
      type="text"
      :placeholder="__('What did you work on?')"
      class="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-slate-700
             bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100
             placeholder-gray-500 dark:placeholder-slate-500 outline-none
             focus:ring-2 focus:ring-[var(--app-accent-500)]/30
             focus:border-[var(--app-accent-500)]"
    />

    <!-- Date + Duration + Start + End -->
    <div class="grid gap-2" :class="hideDate ? 'grid-cols-3' : 'grid-cols-4'">
      <!-- Date (hidden in quick bar) -->
      <div v-if="!hideDate" class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Date') }}</label>
        <input
          v-model="formDate"
          type="date"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                 focus:border-[var(--app-accent-500)]"
        />
      </div>

      <!-- Duration -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Duration') }}</label>
        <input
          v-model="formDuration"
          type="text"
          placeholder="h:mm"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                 focus:border-[var(--app-accent-500)]"
          :class="{ 'border-red-400': formDuration && durationHours === null }"
          @keydown.enter.prevent="handleSave"
        />
      </div>

      <!-- Start -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Start') }}</label>
        <input
          v-model="formStart"
          type="text"
          placeholder="HH:MM"
          maxlength="5"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 tabular-nums outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                 focus:border-[var(--app-accent-500)]"
          :class="{ 'border-red-400': formStart && !isValidTime(formStart) }"
          @blur="formStart = normalizeTimeInput(formStart)"
        />
      </div>

      <!-- End -->
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('End') }}</label>
        <input
          v-model="formEnd"
          type="text"
          placeholder="HH:MM"
          maxlength="5"
          class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 tabular-nums outline-none
                 focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                 focus:border-[var(--app-accent-500)]"
          :class="{ 'border-red-400': formEnd && !isValidTime(formEnd) }"
          @blur="formEnd = normalizeTimeInput(formEnd)"
        />
      </div>
    </div>

    <!-- Tags -->
    <TagInput v-model="formTags" />

    <!-- Budget warning -->
    <div
      v-if="budgetWarning"
      class="text-xs mt-1"
      :class="budgetWarning.b.status === 'exceeded' ? 'text-red-500' : 'text-amber-500'"
    >
      <template v-if="budgetWarning.b.status === 'exceeded'">
        ⚠ {{ __('Budget exceeded') }} — {{ formatHours(budgetWarning.b.used) }}
        {{ __('of') }} {{ formatHours(budgetWarning.b.budget) }} {{ __('used this month') }}
      </template>
      <template v-else>
        ⚠ {{ formatHours(budgetWarning.b.used) }}
        {{ __('of') }} {{ formatHours(budgetWarning.b.budget) }} {{ __('used this month') }}
      </template>
    </div>

    <!-- Entry type -->
    <div class="flex items-center gap-2 flex-wrap">
      <div class="flex gap-1 flex-shrink-0">
        <button
          v-for="opt in ENTRY_OPTIONS"
          :key="opt.value"
          type="button"
          :class="[
            'px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors',
            formType === opt.value
              ? 'bg-[var(--app-accent-500)] border-[var(--app-accent-500)] text-white'
              : 'border-gray-200 dark:border-slate-700 text-gray-600 dark:text-slate-400 hover:border-[var(--app-accent-500)]/50',
          ]"
          @click="formType = opt.value; typeSource = 'manual'"
        >
          {{ __(opt.label) }}
        </button>
      </div>
    </div>

    <!-- Integrations (collapsible, only when configured) -->
    <div v-if="hasLinear || hasGitHub" class="space-y-2">
      <button
        type="button"
        class="text-xs text-gray-500 dark:text-slate-500 hover:text-gray-900 dark:hover:text-slate-100 transition-colors flex items-center gap-1"
        @click="integrationsOpen = !integrationsOpen"
      >
        <span class="inline-block transition-transform" :class="integrationsOpen ? 'rotate-90' : ''">&#9654;</span>
        {{ __('Integrations') }}
      </button>

      <div v-if="integrationsOpen" class="space-y-2 pl-3">
        <!-- Linear issue -->
        <div v-if="hasLinear" class="relative">
          <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Linear Issue') }}</label>
          <input
            v-model="formLinearIssue"
            type="text"
            placeholder="ENG-123"
            class="w-full px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                   focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                   focus:border-[var(--app-accent-500)]"
            @input="searchLinear(formLinearIssue)"
            @blur="dismissLinearSuggestions"
          />
          <ul
            v-if="linearSuggestions.length"
            class="absolute left-0 right-0 top-full mt-1 z-20 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700
                   rounded-lg shadow-lg max-h-40 overflow-y-auto py-1"
          >
            <li
              v-for="item in linearSuggestions"
              :key="item.value"
              class="px-3 py-1.5 text-sm text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer"
              @mousedown.prevent="selectLinear(item)"
            >
              {{ item.label }}
            </li>
          </ul>
        </div>

        <!-- GitHub issue/PR -->
        <div v-if="hasGitHub" class="relative">
          <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('GitHub Issue / PR') }}</label>
          <input
            v-model="formGithubRef"
            type="text"
            placeholder="#42 or owner/repo#42"
            class="w-full px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none
                   focus:ring-2 focus:ring-[var(--app-accent-500)]/30
                   focus:border-[var(--app-accent-500)]"
            @input="searchGitHub(formGithubRef)"
            @blur="dismissGithubSuggestions"
          />
          <ul
            v-if="githubSuggestions.length"
            class="absolute left-0 right-0 top-full mt-1 z-20 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700
                   rounded-lg shadow-lg max-h-40 overflow-y-auto py-1"
          >
            <li
              v-for="item in githubSuggestions"
              :key="item.value"
              class="px-3 py-1.5 text-sm text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer"
              @mousedown.prevent="selectGitHub(item)"
            >
              {{ item.label }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Past-date warning -->
    <p
      v-if="showPastWarning"
      class="text-xs text-amber-500"
    >
      {{ __("You're adding an entry for") }} {{ formDate }} — {{ pastDaysCount }} {{ __('days ago') }}.
    </p>

    <!-- Error -->
    <p v-if="saveError" class="text-xs text-red-500">{{ saveError }}</p>

    <!-- Actions -->
    <div class="flex gap-2">
      <button
        type="button"
        class="flex-1 py-2 rounded-lg border border-gray-200 dark:border-slate-700
               text-sm text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800
               transition-colors"
        @click="emit('cancel')"
      >
        {{ __('Cancel') }}
      </button>
      <button
        type="button"
        class="flex-1 py-2 rounded-lg bg-[var(--app-accent-500)]
               hover:bg-[var(--app-accent-700)] text-white text-sm font-medium
               transition-colors disabled:opacity-50"
        :disabled="!canSave || saving"
        @click="handleSave"
      >
        {{ props.entry ? __('Save changes') : __('Save entry') }}
      </button>
    </div>

  </div>
</template>
