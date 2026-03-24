<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown, ChevronRight, Play, Download } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { formatHours, formatDurationInput } from '@/composables/useEntries'

// ── Types ─────────────────────────────────────────────────────────────────────

interface SummaryEntry {
  name:                    string
  date:                    string
  description:             string
  duration_hours:          number
  entry_status:            'draft' | 'sent'
  contact?:                string | null
  context_type?:           string | null
  context_name?:           string | null
  event_context_name?:     string | null
  event_display?:          string | null
}

interface TaskRow {
  context_name:   string | null
  task_display:   string | null
  hours:          number
  entries:        SummaryEntry[]
}

interface ProjectRow {
  context_name:    string | null
  project_display: string | null
  project_tag:     string | null
  is_tag_based:    boolean
  hours:           number
  tasks:           TaskRow[]
}

interface ContactGroup {
  contact:          string | null
  contact_name:     string | null
  client_tag:       string | null
  client_tag_color: string | null
  is_tag_based:     boolean
  total_hours:      number
  entry_status:     'draft' | 'sent'
  projects:         ProjectRow[]
}

interface FilterOption {
  name:    string
  display: string
}

interface Totals {
  billable_hours:     number
  non_billable_hours: number
  internal_hours:     number
}

interface SummaryData {
  from_date:           string
  to_date:             string
  groups:              ContactGroup[]
  totals:              Totals
  available_contacts:  FilterOption[]
  available_projects:  FilterOption[]
}

interface BillingAction {
  app:      string
  label:    string
  endpoint: string   // dotted python path — called via watch.api.billing.forward_to_app
  icon?:    string
}

// ── Router / query params ─────────────────────────────────────────────────────

const route  = useRoute()
const router = useRouter()

// ── Date range helpers ────────────────────────────────────────────────────────

function todayStr(): string {
  return new Date().toISOString().slice(0, 10)
}

function isoWeekMonday(d: Date = new Date()): string {
  const day = d.getDay() || 7
  const mon = new Date(d)
  mon.setDate(d.getDate() - (day - 1))
  return mon.toISOString().slice(0, 10)
}

function isoWeekSunday(d: Date = new Date()): string {
  const day = d.getDay() || 7
  const sun = new Date(d)
  sun.setDate(d.getDate() + (7 - day))
  return sun.toISOString().slice(0, 10)
}

function addDays(dateStr: string, n: number): string {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + n)
  return d.toISOString().slice(0, 10)
}

function monthRange(monthOffset = 0): [string, string] {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + monthOffset
  const first = new Date(y, m, 1)
  const last  = new Date(y, m + 1, 0)
  return [first.toISOString().slice(0, 10), last.toISOString().slice(0, 10)]
}

function quarterRange(offset = 0): [string, string] {
  const now = new Date()
  const q   = Math.floor(now.getMonth() / 3) + offset
  const y   = now.getFullYear() + Math.floor(q / 4)
  const qn  = ((q % 4) + 4) % 4
  const first = new Date(y, qn * 3, 1)
  const last  = new Date(y, qn * 3 + 3, 0)
  return [first.toISOString().slice(0, 10), last.toISOString().slice(0, 10)]
}

type Preset =
  | 'this_week' | 'last_week'
  | 'this_month' | 'last_month'
  | 'this_quarter' | 'last_quarter'
  | 'this_year'
  | 'custom'

const PRESETS: { value: Preset; label: string }[] = [
  { value: 'this_week',    label: 'This week' },
  { value: 'last_week',    label: 'Last week' },
  { value: 'this_month',   label: 'This month' },
  { value: 'last_month',   label: 'Last month' },
  { value: 'this_quarter', label: 'This quarter' },
  { value: 'last_quarter', label: 'Last quarter' },
  { value: 'this_year',    label: 'This year' },
  { value: 'custom',       label: 'Custom…' },
]

function presetRange(p: Preset): [string, string] {
  const today = todayStr()
  const now   = new Date()
  switch (p) {
    case 'this_week':    return [isoWeekMonday(), isoWeekSunday()]
    case 'last_week': {
      const lastMon = addDays(isoWeekMonday(), -7)
      return [lastMon, addDays(lastMon, 6)]
    }
    case 'this_month':   return monthRange(0)
    case 'last_month':   return monthRange(-1)
    case 'this_quarter': return quarterRange(0)
    case 'last_quarter': return quarterRange(-1)
    case 'this_year':    return [`${now.getFullYear()}-01-01`, today]
    default:             return [isoWeekMonday(), today]
  }
}

// ── State ─────────────────────────────────────────────────────────────────────

// Initialise from URL or default to this week
const initFrom = (route.query.from as string) || isoWeekMonday()
const initTo   = (route.query.to   as string) || isoWeekSunday()

const fromDate      = ref(initFrom)
const toDate        = ref(initTo)
const activePreset  = ref<Preset>('this_week')
const presetOpen    = ref(false)

interface BudgetStatus {
  used: number
  budget: number
  pct: number | null
  status: 'none' | 'approaching' | 'exceeded'
  threshold_pct: number
}

const summaryData   = ref<SummaryData | null>(null)
const groupBudgets  = ref<Record<string, BudgetStatus>>({})
const loading       = ref(false)
const apiError      = ref<string | null>(null)

// Context filters
const filterContact = ref<string>('')
const filterProject = ref<string>('')

const billingActions = ref<BillingAction[]>([])
const sendMenuOpen   = ref<string | null>(null)  // group key of open send menu
const sending        = ref<string | null>(null)  // group key currently sending
const sendingAll     = ref(false)
const sendAllOpen    = ref(false)

interface Confirmation {
  hours:     number
  label:     string
  draft_url: string | null
}
const lastConfirm = ref<Confirmation | null>(null)

// Collapsed state: true = collapsed (default)
const collapsed = ref<Record<string, boolean>>({})

// Project-level expand: false = collapsed (default)
const projectExpanded = ref<Record<string, boolean>>({})

// Task-level expand: false = collapsed (default)
const taskExpanded = ref<Record<string, boolean>>({})

// Custom date picker visibility
const showCustomPickers = ref(false)

// ── URL sync ──────────────────────────────────────────────────────────────────

function pushUrl() {
  router.replace({ path: '/watch/prepare', query: { from: fromDate.value, to: toDate.value } })
}

// ── Load ──────────────────────────────────────────────────────────────────────

async function loadGroupBudgets() {
  try {
    const res  = await fetch('/api/method/watch.api.tags.get_all_budgets', {
      headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    })
    const data = await res.json()
    groupBudgets.value = data.message ?? {}
  } catch { /* non-critical */ }
}

async function load() {
  loading.value  = true
  apiError.value = null
  try {
    const params = new URLSearchParams({ from_date: fromDate.value, to_date: toDate.value })
    if (filterContact.value) params.set('contact', filterContact.value)
    if (filterProject.value) params.set('context_name', filterProject.value)
    const res  = await fetch(`/api/method/watch.api.billing.get_summary?${params}`, {
      headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Load failed')
    summaryData.value = data.message as SummaryData
    // Initialise all groups as collapsed
    const col: Record<string, boolean> = {}
    for (const g of (summaryData.value?.groups ?? [])) {
      col[groupKey(g)] = true
    }
    collapsed.value = col
    projectExpanded.value = {}
    taskExpanded.value = {}
    loadGroupBudgets()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadBillingActions() {
  try {
    const res  = await fetch('/api/method/watch.api.billing.get_billing_actions', {
      headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    })
    const data = await res.json()
    billingActions.value = data.message ?? []
  } catch { /* ignore */ }
}

onMounted(() => {
  load()
  loadBillingActions()
})

// ── Date range changes ────────────────────────────────────────────────────────

function applyPreset(p: Preset) {
  activePreset.value = p
  presetOpen.value   = false
  if (p === 'custom') {
    showCustomPickers.value = true
    return
  }
  showCustomPickers.value = false
  const [f, t] = presetRange(p)
  fromDate.value = f
  toDate.value   = t
  pushUrl()
  load()
}

function applyCustomRange() {
  if (!fromDate.value || !toDate.value) return
  activePreset.value = 'custom'
  pushUrl()
  load()
}

// Keep preset in sync when URL changes externally
watch([() => route.query.from, () => route.query.to], ([f, t]) => {
  if (f && t && (f !== fromDate.value || t !== toDate.value)) {
    fromDate.value = f as string
    toDate.value   = t as string
    load()
  }
})

// ── Group helpers ─────────────────────────────────────────────────────────────

function groupKey(g: ContactGroup): string {
  if (g.contact) return `contact:${g.contact}`
  return g.client_tag ?? '__unassigned__'
}

function groupLabel(g: ContactGroup): string {
  return g.contact_name ?? g.client_tag ?? __('(no contact)')
}

function chipStyle(color: string | null) {
  const c = color || 'var(--app-accent-500)'
  return { backgroundColor: `${c}22`, color: c, borderColor: `${c}44` }
}

function toggleCollapse(g: ContactGroup) {
  const key = groupKey(g)
  collapsed.value[key] = !collapsed.value[key]
}

function projectKey(g: ContactGroup, p: ProjectRow): string {
  return `${groupKey(g)}::${p.context_name ?? p.project_tag ?? '__none__'}`
}

function toggleProject(g: ContactGroup, p: ProjectRow) {
  const key = projectKey(g, p)
  projectExpanded.value[key] = !projectExpanded.value[key]
}

function taskKey(g: ContactGroup, p: ProjectRow, t: TaskRow): string {
  return `${projectKey(g, p)}::${t.context_name ?? '__none__'}`
}

function toggleTask(g: ContactGroup, p: ProjectRow, t: TaskRow) {
  const key = taskKey(g, p, t)
  taskExpanded.value[key] = !taskExpanded.value[key]
}

function projectLabel(p: ProjectRow): string {
  return p.project_display ?? p.project_tag ?? __('(no project)')
}

function onFilterChange() {
  load()
}

// ── Send actions ──────────────────────────────────────────────────────────────

function openSendMenu(g: ContactGroup, e: MouseEvent) {
  e.stopPropagation()
  const key = groupKey(g)
  if (sendMenuOpen.value === key) {
    sendMenuOpen.value = null
    return
  }
  sendMenuOpen.value = key
  setTimeout(() => window.addEventListener('click', () => { sendMenuOpen.value = null }, { once: true }), 0)
}

function openSendAllMenu(e: MouseEvent) {
  e.stopPropagation()
  sendAllOpen.value = !sendAllOpen.value
  if (sendAllOpen.value) {
    setTimeout(() => window.addEventListener('click', () => { sendAllOpen.value = false }, { once: true }), 0)
  }
}

// Shared: call forward_to_app.
async function callForwardToApp(
  action: BillingAction,
  clientTag: string | null,
  contact: string | null = null,
): Promise<{ forwarded_hours: number; draft_url: string | null }> {
  const body: Record<string, unknown> = {
    action_endpoint: action.endpoint,
    from_date:       fromDate.value,
    to_date:         toDate.value,
  }
  if (clientTag !== null) body.client_tag = clientTag
  if (contact) body.contact = contact
  const res  = await fetch('/api/method/watch.api.billing.forward_to_app', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    body:    JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok || data.exc) throw new Error(data.exc ?? __('Send failed'))
  return data.message
}

// Shared: call export_csv.
async function callExportCsv(clientTag: string | null, contact: string | null = null): Promise<void> {
  const body: Record<string, unknown> = {
    from_date: fromDate.value,
    to_date:   toDate.value,
  }
  if (clientTag !== null) body.client_tag = clientTag
  if (contact) body.contact = contact
  const res  = await fetch('/api/method/watch.api.billing.export_csv', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    body:    JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok || data.exc) throw new Error(data.exc ?? __('Export failed'))
  const { csv, filename } = data.message
  const blob = new Blob([csv], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function doSend(g: ContactGroup, action: BillingAction) {
  const key = groupKey(g)
  sendMenuOpen.value = null
  sending.value      = key
  apiError.value     = null
  lastConfirm.value  = null
  try {
    const result = await callForwardToApp(action, g.client_tag ?? '', g.contact)
    lastConfirm.value = { hours: result.forwarded_hours, label: action.label, draft_url: result.draft_url }
    await load()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    sending.value = null
  }
}

async function doExportCsv(g: ContactGroup) {
  sendMenuOpen.value = null
  sending.value      = groupKey(g)
  apiError.value     = null
  lastConfirm.value  = null
  try {
    await callExportCsv(g.client_tag ?? '', g.contact)
    await load()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    sending.value = null
  }
}

async function doSendAll(action: BillingAction) {
  sendAllOpen.value  = false
  sendingAll.value   = true
  apiError.value     = null
  lastConfirm.value  = null
  try {
    // null = all clients (no client_tag filter)
    const result = await callForwardToApp(action, null)
    lastConfirm.value = { hours: result.forwarded_hours, label: action.label, draft_url: result.draft_url }
    await load()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    sendingAll.value = false
  }
}

async function doExportAll() {
  sendAllOpen.value  = false
  sendingAll.value   = true
  apiError.value     = null
  lastConfirm.value  = null
  try {
    await callExportCsv(null)
    await load()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    sendingAll.value = false
  }
}

// ── General CSV export ────────────────────────────────────────────────────────

function downloadGeneralCsv() {
  const params = new URLSearchParams({ from_date: fromDate.value, to_date: toDate.value })
  window.location.href = `/api/method/watch.api.time_entry.export_csv?${params}`
}

// ── Formatted helpers ─────────────────────────────────────────────────────────

const activePresetLabel = computed(
  () => PRESETS.find(p => p.value === activePreset.value)?.label ?? __('Custom…'),
)

function fmtDate(d: string): string {
  return new Date(d + 'T00:00:00').toLocaleDateString(undefined, {
    weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
  })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-slate-800">
    <div class="max-w-2xl mx-auto px-4 py-6 space-y-4">

      <!-- Page heading -->
      <h1 class="text-lg font-semibold text-gray-900 dark:text-slate-100">
        {{ __('Prepare Draft') }}
      </h1>

      <!-- Date range bar -->
      <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 px-4 py-3 space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <!-- From date -->
          <input
            v-model="fromDate"
            type="date"
            :max="toDate"
            class="px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none
                   focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
            @change="activePreset = 'custom'; showCustomPickers = true"
          />
          <span class="text-gray-500 dark:text-slate-500 text-sm">→</span>
          <!-- To date -->
          <input
            v-model="toDate"
            type="date"
            :min="fromDate"
            class="px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none
                   focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
            @change="activePreset = 'custom'; showCustomPickers = true"
          />

          <!-- Preset dropdown -->
          <div class="relative ml-auto">
            <button
              type="button"
              class="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                     text-sm text-gray-900 dark:text-slate-100 hover:border-[var(--app-accent-500)]/50 transition-colors"
              @click="presetOpen = !presetOpen"
            >
              {{ __(activePresetLabel) }}
              <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <div
              v-if="presetOpen"
              class="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700
                     rounded-xl shadow-lg py-1 min-w-[160px]"
            >
              <button
                v-for="p in PRESETS"
                :key="p.value"
                type="button"
                :class="[
                  'w-full text-left px-3 py-1.5 text-sm transition-colors',
                  activePreset === p.value
                    ? 'text-[var(--app-accent-500)] font-medium'
                    : 'text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800',
                ]"
                @click="applyPreset(p.value)"
              >
                {{ __(p.label) }}
              </button>
            </div>
          </div>

          <!-- Apply button for custom range -->
          <button
            v-if="activePreset === 'custom'"
            type="button"
            class="px-3 py-1.5 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                   text-white text-sm font-medium transition-colors"
            @click="applyCustomRange"
          >
            {{ __('Apply') }}
          </button>

          <!-- General export CSV (all entry types, no billing side-effects) -->
          <button
            type="button"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                   text-sm text-gray-500 dark:text-slate-500 hover:bg-gray-50 dark:hover:bg-slate-800
                   transition-colors"
            :title="__('Download all entries for this period as CSV')"
            @click="downloadGeneralCsv"
          >
            <Download class="w-3.5 h-3.5" aria-hidden="true" />
            {{ __('Export CSV') }}
          </button>
        </div>

        <!-- Context filters -->
        <div
          v-if="summaryData && (summaryData.available_contacts.length > 0 || summaryData.available_projects.length > 0)"
          class="flex flex-wrap items-center gap-2 pt-1"
        >
          <span class="text-xs text-gray-500 dark:text-slate-500">{{ __('Filter by:') }}</span>
          <select
            v-if="summaryData.available_contacts.length > 0"
            v-model="filterContact"
            class="px-2 py-1 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none"
            @change="onFilterChange"
          >
            <option value="">{{ __('All contacts') }}</option>
            <option v-for="c in summaryData.available_contacts" :key="c.name" :value="c.name">
              {{ c.display }}
            </option>
          </select>
          <select
            v-if="summaryData.available_projects.length > 0"
            v-model="filterProject"
            class="px-2 py-1 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                   bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none"
            @change="onFilterChange"
          >
            <option value="">{{ __('All projects') }}</option>
            <option v-for="p in summaryData.available_projects" :key="p.name" :value="p.name">
              {{ p.display }}
            </option>
          </select>
        </div>
      </div>

      <!-- API error -->
      <p v-if="apiError" class="text-sm text-red-500 px-1">{{ apiError }}</p>

      <!-- Confirmation banner -->
      <div
        v-if="lastConfirm"
        class="flex items-center gap-3 px-4 py-3 rounded-xl border border-green-300
               bg-green-50 text-green-800 dark:border-green-700 dark:bg-green-900/20 dark:text-green-300 text-sm"
      >
        <span class="flex-1">
          {{ __('Forwarded {0} to {1}', [formatHours(lastConfirm.hours), lastConfirm.label]) }}
        </span>
        <a
          v-if="lastConfirm.draft_url"
          :href="lastConfirm.draft_url"
          target="_blank"
          rel="noopener noreferrer"
          class="underline font-medium shrink-0"
        >
          {{ __('Open draft') }}
        </a>
        <button
          type="button"
          class="shrink-0 text-green-600 hover:text-green-800 dark:text-green-400"
          :title="__('Dismiss')"
          @click="lastConfirm = null"
        >
          ×
        </button>
      </div>

      <!-- Loading skeleton -->
      <template v-if="loading">
        <div
          v-for="i in 2"
          :key="i"
          class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 p-4 animate-pulse"
        >
          <div class="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mb-2" />
          <div class="h-3 bg-gray-200 dark:bg-slate-700 rounded w-1/2" />
        </div>
      </template>

      <!-- Empty state -->
      <div
        v-else-if="!loading && summaryData && !summaryData.groups.length"
        class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
               p-8 text-center text-sm text-gray-500 dark:text-slate-500"
      >
        {{ __('No billable entries for this period.') }}
      </div>

      <!-- Contact/Client groups (3-level hierarchy) -->
      <template v-else-if="summaryData">
        <div
          v-for="group in summaryData.groups"
          :key="groupKey(group)"
          class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden"
        >
          <!-- Level 1: Contact/Client header row -->
          <div
            class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            @click="toggleCollapse(group)"
          >
            <component
              :is="collapsed[groupKey(group)] ? ChevronRight : ChevronDown"
              class="w-4 h-4 shrink-0 text-gray-500 dark:text-slate-500"
              aria-hidden="true"
            />

            <!-- Contact name or Client tag chip -->
            <span
              v-if="group.is_tag_based && group.client_tag"
              class="text-xs font-medium px-2 py-0.5 rounded border shrink-0"
              :style="chipStyle(group.client_tag_color)"
            >
              {{ group.client_tag }}
            </span>
            <span
              v-else
              class="text-sm font-medium text-gray-900 dark:text-slate-100 shrink-0"
            >
              {{ groupLabel(group) }}
            </span>

            <!-- Hours -->
            <span class="text-sm font-semibold text-gray-900 dark:text-slate-100">
              {{ formatHours(group.total_hours) }}
            </span>

            <!-- Sent badge -->
            <span
              v-if="group.entry_status === 'sent'"
              class="ml-auto text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700
                     dark:bg-green-900/30 dark:text-green-400 shrink-0"
            >
              {{ __('Sent') }}
            </span>

            <!-- Send button -->
            <div
              v-else
              class="ml-auto relative shrink-0"
              @click.stop
            >
              <!-- No invoicing apps → CSV export -->
              <button
                v-if="!billingActions.length"
                type="button"
                :disabled="sending === groupKey(group)"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                       text-sm text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800
                       transition-colors disabled:opacity-50"
                @click="doExportCsv(group)"
              >
                <Download class="w-3.5 h-3.5" aria-hidden="true" />
                {{ __('Export CSV') }}
              </button>

              <!-- Single invoicing app → direct send -->
              <button
                v-else-if="billingActions.length === 1"
                type="button"
                :disabled="sending === groupKey(group)"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                       bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                       text-white text-sm font-medium transition-colors disabled:opacity-50"
                @click="doSend(group, billingActions[0])"
              >
                <Play class="w-3.5 h-3.5" aria-hidden="true" />
                {{ __('Send to {0}', [billingActions[0].label]) }}
              </button>

              <!-- Multiple apps → dropdown -->
              <div v-else>
                <button
                  type="button"
                  :disabled="sending === groupKey(group)"
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                         bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                         text-white text-sm font-medium transition-colors disabled:opacity-50"
                  @click="openSendMenu(group, $event)"
                >
                  <Play class="w-3.5 h-3.5" aria-hidden="true" />
                  {{ __('Send') }}
                  <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
                </button>
                <div
                  v-if="sendMenuOpen === groupKey(group)"
                  class="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-slate-950
                         border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg py-1 min-w-[160px]"
                >
                  <button
                    v-for="action in billingActions"
                    :key="action.app"
                    type="button"
                    class="w-full text-left px-3 py-1.5 text-sm text-gray-900 dark:text-slate-100
                           hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                    @click="doSend(group, action)"
                  >
                    {{ __('Send to {0}', [action.label]) }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Budget warning (always visible, non-blocking) -->
          <div
            v-if="group.client_tag && groupBudgets[group.client_tag] && groupBudgets[group.client_tag].status !== 'none'"
            class="px-4 py-2 border-t border-gray-200 dark:border-slate-700"
            :class="groupBudgets[group.client_tag].status === 'exceeded' ? 'bg-red-50 dark:bg-red-900/10' : 'bg-amber-50 dark:bg-amber-900/10'"
          >
            <span
              class="text-xs"
              :class="groupBudgets[group.client_tag].status === 'exceeded' ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'"
            >
              <template v-if="groupBudgets[group.client_tag].status === 'exceeded'">
                {{ __('Budget exceeded') }} —
                {{ formatHours(groupBudgets[group.client_tag].used) }}
                {{ __('of') }}
                {{ formatHours(groupBudgets[group.client_tag].budget) }}
                {{ __('used this month') }}
              </template>
              <template v-else>
                {{ formatHours(groupBudgets[group.client_tag].used) }}
                {{ __('of') }}
                {{ formatHours(groupBudgets[group.client_tag].budget) }}
                {{ __('budget used this month') }}
                ({{ groupBudgets[group.client_tag].pct }}%)
              </template>
            </span>
          </div>

          <!-- Level 2: Project sub-rows -->
          <div
            v-if="!collapsed[groupKey(group)]"
            class="border-t border-gray-200 dark:border-slate-700"
          >
            <template
              v-for="project in group.projects"
              :key="projectKey(group, project)"
            >
              <!-- Project row — clickable to expand tasks/entries -->
              <div
                class="flex items-center gap-3 px-4 py-2.5 pl-8
                       border-b border-gray-200 dark:border-slate-700
                       text-sm text-gray-500 dark:text-slate-500 cursor-pointer
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="toggleProject(group, project)"
              >
                <component
                  :is="projectExpanded[projectKey(group, project)] ? ChevronDown : ChevronRight"
                  class="w-3.5 h-3.5 shrink-0"
                  aria-hidden="true"
                />
                <span
                  v-if="project.is_tag_based && project.project_tag"
                  class="flex-1 text-gray-900 dark:text-slate-100 italic"
                >
                  {{ project.project_tag }}
                </span>
                <span v-else class="flex-1 text-gray-900 dark:text-slate-100">
                  {{ projectLabel(project) }}
                </span>
                <span>{{ formatHours(project.hours) }}</span>
              </div>

              <!-- Level 3: Tasks + entries (expanded) -->
              <div
                v-if="projectExpanded[projectKey(group, project)]"
                class="border-b border-gray-200 dark:border-slate-700"
              >
                <template
                  v-for="task in project.tasks"
                  :key="taskKey(group, project, task)"
                >
                  <!-- Task row (only if task has a name, otherwise entries are directly under project) -->
                  <div
                    v-if="task.context_name"
                    class="flex items-center gap-3 px-4 py-2 pl-12
                           text-sm text-gray-500 dark:text-slate-500 cursor-pointer
                           hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors
                           border-b border-gray-200 dark:border-slate-700"
                    @click="toggleTask(group, project, task)"
                  >
                    <component
                      :is="taskExpanded[taskKey(group, project, task)] ? ChevronDown : ChevronRight"
                      class="w-3 h-3 shrink-0"
                      aria-hidden="true"
                    />
                    <span class="flex-1 text-gray-900 dark:text-slate-100">
                      {{ task.task_display ?? __('(no task)') }}
                    </span>
                    <span class="text-xs">{{ formatHours(task.hours) }}</span>
                  </div>

                  <!-- Entry rows (shown directly when no task, or when task is expanded) -->
                  <div
                    v-if="!task.context_name || taskExpanded[taskKey(group, project, task)]"
                    class="bg-gray-50 dark:bg-slate-800"
                  >
                    <div
                      v-for="entry in task.entries"
                      :key="entry.name"
                      class="px-4 py-1.5 text-xs border-t border-gray-200 dark:border-slate-700"
                      :class="task.context_name ? 'pl-[4.5rem]' : 'pl-14'"
                    >
                      <div class="flex items-center gap-2">
                        <span class="flex-1 text-gray-900 dark:text-slate-100 truncate">
                          {{ entry.description || __('(no description)') }}
                        </span>
                        <span class="w-12 text-right text-gray-500 dark:text-slate-500 shrink-0">
                          {{ formatDurationInput(entry.duration_hours) }}
                        </span>
                      </div>
                      <!-- Event context detail -->
                      <div
                        v-if="entry.event_display"
                        class="text-[0.625rem] text-gray-500 dark:text-slate-500 mt-0.5"
                      >
                        {{ entry.event_display }} ({{ __('Event') }})
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>

        <!-- Global send button — only when there are ≥2 draft groups -->
        <div
          v-if="summaryData.groups.filter(g => g.entry_status === 'draft').length > 1"
          class="flex justify-end"
          @click.stop
        >
          <!-- No billing actions → Export All CSV -->
          <button
            v-if="!billingActions.length"
            type="button"
            :disabled="sendingAll"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                   text-sm text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800
                   transition-colors disabled:opacity-50"
            @click="doExportAll"
          >
            <Download class="w-3.5 h-3.5" aria-hidden="true" />
            {{ __('Export All CSV') }}
          </button>

          <!-- Single app → direct send all -->
          <button
            v-else-if="billingActions.length === 1"
            type="button"
            :disabled="sendingAll"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                   bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                   text-white text-sm font-medium transition-colors disabled:opacity-50"
            @click="doSendAll(billingActions[0])"
          >
            <Play class="w-3.5 h-3.5" aria-hidden="true" />
            {{ __('Send All to {0}', [billingActions[0].label]) }}
          </button>

          <!-- Multiple apps → dropdown -->
          <div v-else class="relative">
            <button
              type="button"
              :disabled="sendingAll"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                     bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                     text-white text-sm font-medium transition-colors disabled:opacity-50"
              @click="openSendAllMenu($event)"
            >
              <Play class="w-3.5 h-3.5" aria-hidden="true" />
              {{ __('Send All') }}
              <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <div
              v-if="sendAllOpen"
              class="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-slate-950
                     border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg py-1 min-w-[180px]"
            >
              <button
                v-for="action in billingActions"
                :key="action.app"
                type="button"
                class="w-full text-left px-3 py-1.5 text-sm text-gray-900 dark:text-slate-100
                       hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                @click="doSendAll(action)"
              >
                {{ __('Send All to {0}', [action.label]) }}
              </button>
            </div>
          </div>
        </div>

        <!-- Footer totals -->
        <div
          class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700
                 px-4 py-3 space-y-1.5 text-sm"
        >
          <!-- Total billable -->
          <div class="flex items-center gap-4">
            <span class="text-gray-500 dark:text-slate-500 flex-1">{{ __('Total billable') }}</span>
            <span class="font-semibold text-gray-900 dark:text-slate-100">
              {{ formatHours(summaryData.totals.billable_hours) }}
            </span>
          </div>

          <!-- Internal -->
          <div
            v-if="summaryData.totals.internal_hours"
            class="flex items-center gap-4 text-gray-500 dark:text-slate-500"
          >
            <span class="flex-1">{{ __('Internal / overhead') }}</span>
            <span>{{ formatHours(summaryData.totals.internal_hours) }}</span>
            <span class="italic">{{ __('(not billed)') }}</span>
          </div>

          <!-- Non-billable -->
          <div
            v-if="summaryData.totals.non_billable_hours"
            class="flex items-center gap-4 text-gray-500 dark:text-slate-500"
          >
            <span class="flex-1">{{ __('Non-billable') }}</span>
            <span>{{ formatHours(summaryData.totals.non_billable_hours) }}</span>
            <span class="italic">{{ __('(not billed)') }}</span>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>
