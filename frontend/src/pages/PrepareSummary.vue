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
}

interface ProjectRow {
  project_tag:    string | null
  hours:          number
  entries:        SummaryEntry[]
}

interface ClientGroup {
  client_tag:       string | null
  client_tag_color: string | null
  total_hours:      number
  entry_status:     'draft' | 'sent'
  projects:         ProjectRow[]
}

interface Totals {
  billable_hours:     number
  non_billable_hours: number
  internal_hours:     number
}

interface SummaryData {
  from_date: string
  to_date:   string
  groups:    ClientGroup[]
  totals:    Totals
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

const billingActions = ref<BillingAction[]>([])
const sendMenuOpen   = ref<string | null>(null)  // client_tag key of open send menu
const sending        = ref<string | null>(null)  // client_tag key currently sending
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

function groupKey(g: ClientGroup): string {
  return g.client_tag ?? '__unassigned__'
}

function chipStyle(color: string | null) {
  const c = color || 'var(--watch-primary)'
  return { backgroundColor: `${c}22`, color: c, borderColor: `${c}44` }
}

function toggleCollapse(g: ClientGroup) {
  const key = groupKey(g)
  collapsed.value[key] = !collapsed.value[key]
}

function projectKey(g: ClientGroup, p: ProjectRow): string {
  return `${groupKey(g)}::${p.project_tag ?? '__none__'}`
}

function toggleProject(g: ClientGroup, p: ProjectRow) {
  const key = projectKey(g, p)
  projectExpanded.value[key] = !projectExpanded.value[key]
}

// ── Send actions ──────────────────────────────────────────────────────────────

function openSendMenu(g: ClientGroup, e: MouseEvent) {
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
// clientTag: null = all clients, '' = unassigned, non-empty = specific client.
async function callForwardToApp(
  action: BillingAction,
  clientTag: string | null,
): Promise<{ forwarded_hours: number; draft_url: string | null }> {
  const body: Record<string, unknown> = {
    action_endpoint: action.endpoint,
    from_date:       fromDate.value,
    to_date:         toDate.value,
  }
  if (clientTag !== null) body.client_tag = clientTag
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
// clientTag: null = all clients, '' = unassigned, non-empty = specific client.
async function callExportCsv(clientTag: string | null): Promise<void> {
  const body: Record<string, unknown> = {
    from_date: fromDate.value,
    to_date:   toDate.value,
  }
  if (clientTag !== null) body.client_tag = clientTag
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

async function doSend(g: ClientGroup, action: BillingAction) {
  const key = groupKey(g)
  sendMenuOpen.value = null
  sending.value      = key
  apiError.value     = null
  lastConfirm.value  = null
  try {
    const result = await callForwardToApp(action, g.client_tag ?? '')
    lastConfirm.value = { hours: result.forwarded_hours, label: action.label, draft_url: result.draft_url }
    await load()
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    sending.value = null
  }
}

async function doExportCsv(g: ClientGroup) {
  sendMenuOpen.value = null
  sending.value      = groupKey(g)
  apiError.value     = null
  lastConfirm.value  = null
  try {
    await callExportCsv(g.client_tag ?? '')
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
  <div class="min-h-screen bg-[var(--watch-bg-secondary)]">
    <div class="max-w-2xl mx-auto px-4 py-6 space-y-4">

      <!-- Page heading -->
      <h1 class="text-lg font-semibold text-[var(--watch-text)]">
        {{ __('Prepare Draft') }}
      </h1>

      <!-- Date range bar -->
      <div class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] px-4 py-3 space-y-3">
        <div class="flex flex-wrap items-center gap-2">
          <!-- From date -->
          <input
            v-model="fromDate"
            type="date"
            :max="toDate"
            class="px-2 py-1.5 text-sm rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-[var(--watch-text)] outline-none
                   focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
            @change="activePreset = 'custom'; showCustomPickers = true"
          />
          <span class="text-[var(--watch-text-muted)] text-sm">→</span>
          <!-- To date -->
          <input
            v-model="toDate"
            type="date"
            :min="fromDate"
            class="px-2 py-1.5 text-sm rounded-lg border border-[var(--watch-border)]
                   bg-[var(--watch-bg)] text-[var(--watch-text)] outline-none
                   focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
            @change="activePreset = 'custom'; showCustomPickers = true"
          />

          <!-- Preset dropdown -->
          <div class="relative ml-auto">
            <button
              type="button"
              class="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                     text-sm text-[var(--watch-text)] hover:border-[var(--watch-primary)]/50 transition-colors"
              @click="presetOpen = !presetOpen"
            >
              {{ __(activePresetLabel) }}
              <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <div
              v-if="presetOpen"
              class="absolute right-0 top-full mt-1 z-20 bg-[var(--watch-bg)] border border-[var(--watch-border)]
                     rounded-xl shadow-lg py-1 min-w-[160px]"
            >
              <button
                v-for="p in PRESETS"
                :key="p.value"
                type="button"
                :class="[
                  'w-full text-left px-3 py-1.5 text-sm transition-colors',
                  activePreset === p.value
                    ? 'text-[var(--watch-primary)] font-medium'
                    : 'text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)]',
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
            class="px-3 py-1.5 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                   text-white text-sm font-medium transition-colors"
            @click="applyCustomRange"
          >
            {{ __('Apply') }}
          </button>

          <!-- General export CSV (all entry types, no billing side-effects) -->
          <button
            type="button"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                   text-sm text-[var(--watch-text-muted)] hover:bg-[var(--watch-bg-secondary)]
                   transition-colors"
            :title="__('Download all entries for this period as CSV')"
            @click="downloadGeneralCsv"
          >
            <Download class="w-3.5 h-3.5" aria-hidden="true" />
            {{ __('Export CSV') }}
          </button>
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
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-4 animate-pulse"
        >
          <div class="h-4 bg-[var(--watch-border)] rounded w-1/3 mb-2" />
          <div class="h-3 bg-[var(--watch-border)] rounded w-1/2" />
        </div>
      </template>

      <!-- Empty state -->
      <div
        v-else-if="!loading && summaryData && !summaryData.groups.length"
        class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
               p-8 text-center text-sm text-[var(--watch-text-muted)]"
      >
        {{ __('No billable entries for this period.') }}
      </div>

      <!-- Client groups -->
      <template v-else-if="summaryData">
        <div
          v-for="group in summaryData.groups"
          :key="groupKey(group)"
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden"
        >
          <!-- Client header row -->
          <div
            class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-[var(--watch-bg-secondary)] transition-colors"
            @click="toggleCollapse(group)"
          >
            <component
              :is="collapsed[groupKey(group)] ? ChevronRight : ChevronDown"
              class="w-4 h-4 shrink-0 text-[var(--watch-text-muted)]"
              aria-hidden="true"
            />

            <!-- Client chip -->
            <span
              class="text-xs font-medium px-2 py-0.5 rounded border shrink-0"
              :style="chipStyle(group.client_tag_color)"
            >
              {{ group.client_tag ?? __('Unassigned') }}
            </span>

            <!-- Hours -->
            <span class="text-sm font-semibold text-[var(--watch-text)]">
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
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                       text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
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
                       bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
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
                         bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                         text-white text-sm font-medium transition-colors disabled:opacity-50"
                  @click="openSendMenu(group, $event)"
                >
                  <Play class="w-3.5 h-3.5" aria-hidden="true" />
                  {{ __('Send') }}
                  <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
                </button>
                <div
                  v-if="sendMenuOpen === groupKey(group)"
                  class="absolute right-0 top-full mt-1 z-20 bg-[var(--watch-bg)]
                         border border-[var(--watch-border)] rounded-xl shadow-lg py-1 min-w-[160px]"
                >
                  <button
                    v-for="action in billingActions"
                    :key="action.app"
                    type="button"
                    class="w-full text-left px-3 py-1.5 text-sm text-[var(--watch-text)]
                           hover:bg-[var(--watch-bg-secondary)] transition-colors"
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
            class="px-4 py-2 border-t border-[var(--watch-border)]"
            :class="groupBudgets[group.client_tag].status === 'exceeded' ? 'bg-red-50 dark:bg-red-900/10' : 'bg-amber-50 dark:bg-amber-900/10'"
          >
            <span
              class="text-xs"
              :class="groupBudgets[group.client_tag].status === 'exceeded' ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'"
            >
              <template v-if="groupBudgets[group.client_tag].status === 'exceeded'">
                🔴 {{ __('Budget exceeded') }} —
                {{ formatHours(groupBudgets[group.client_tag].used) }}
                {{ __('of') }}
                {{ formatHours(groupBudgets[group.client_tag].budget) }}
                {{ __('used this month') }}
              </template>
              <template v-else>
                ⚠ {{ formatHours(groupBudgets[group.client_tag].used) }}
                {{ __('of') }}
                {{ formatHours(groupBudgets[group.client_tag].budget) }}
                {{ __('budget used this month') }}
                ({{ groupBudgets[group.client_tag].pct }}%)
              </template>
            </span>
          </div>

          <!-- Project sub-rows -->
          <div
            v-if="!collapsed[groupKey(group)]"
            class="border-t border-[var(--watch-border)]"
          >
            <template
              v-for="project in group.projects"
              :key="project.project_tag ?? '__none__'"
            >
              <!-- Project row — clickable to expand entries -->
              <div
                class="flex items-center gap-3 px-4 py-2.5 pl-8
                       border-b border-[var(--watch-border)]
                       text-sm text-[var(--watch-text-muted)] cursor-pointer
                       hover:bg-[var(--watch-bg-secondary)] transition-colors"
                @click="toggleProject(group, project)"
              >
                <component
                  :is="projectExpanded[projectKey(group, project)] ? ChevronDown : ChevronRight"
                  class="w-3.5 h-3.5 shrink-0"
                  aria-hidden="true"
                />
                <span class="flex-1 text-[var(--watch-text)]">
                  {{ project.project_tag ?? __('(untagged project)') }}
                </span>
                <span>{{ formatHours(project.hours) }}</span>
              </div>

              <!-- Entry detail table (expanded) -->
              <div
                v-if="projectExpanded[projectKey(group, project)]"
                class="border-b border-[var(--watch-border)] bg-[var(--watch-bg-secondary)]"
              >
                <!-- Header row -->
                <div class="flex items-center gap-2 px-4 py-1.5 pl-14 text-xs text-[var(--watch-text-muted)] font-medium">
                  <span class="flex-1">{{ __('Description') }}</span>
                  <span class="w-12 text-right">{{ __('Duration') }}</span>
                </div>
                <!-- Entry rows -->
                <div
                  v-for="e in project.entries"
                  :key="e.name"
                  class="flex items-center gap-2 px-4 py-1.5 pl-14 text-xs border-t border-[var(--watch-border)]"
                >
                  <span class="flex-1 text-[var(--watch-text)] truncate">
                    {{ e.description || __('(no description)') }}
                  </span>
                  <span class="w-12 text-right text-[var(--watch-text-muted)]">
                    {{ formatDurationInput(e.duration_hours) }}
                  </span>
                </div>
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
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--watch-border)]
                   text-sm text-[var(--watch-text-secondary)] hover:bg-[var(--watch-bg-secondary)]
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
                   bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
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
                     bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)]
                     text-white text-sm font-medium transition-colors disabled:opacity-50"
              @click="openSendAllMenu($event)"
            >
              <Play class="w-3.5 h-3.5" aria-hidden="true" />
              {{ __('Send All') }}
              <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <div
              v-if="sendAllOpen"
              class="absolute right-0 top-full mt-1 z-20 bg-[var(--watch-bg)]
                     border border-[var(--watch-border)] rounded-xl shadow-lg py-1 min-w-[180px]"
            >
              <button
                v-for="action in billingActions"
                :key="action.app"
                type="button"
                class="w-full text-left px-3 py-1.5 text-sm text-[var(--watch-text)]
                       hover:bg-[var(--watch-bg-secondary)] transition-colors"
                @click="doSendAll(action)"
              >
                {{ __('Send All to {0}', [action.label]) }}
              </button>
            </div>
          </div>
        </div>

        <!-- Footer totals -->
        <div
          class="bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)]
                 px-4 py-3 space-y-1.5 text-sm"
        >
          <!-- Total billable -->
          <div class="flex items-center gap-4">
            <span class="text-[var(--watch-text-muted)] flex-1">{{ __('Total billable') }}</span>
            <span class="font-semibold text-[var(--watch-text)]">
              {{ formatHours(summaryData.totals.billable_hours) }}
            </span>
          </div>

          <!-- Internal -->
          <div
            v-if="summaryData.totals.internal_hours"
            class="flex items-center gap-4 text-[var(--watch-text-muted)]"
          >
            <span class="flex-1">{{ __('Internal / overhead') }}</span>
            <span>{{ formatHours(summaryData.totals.internal_hours) }}</span>
            <span class="italic">{{ __('(not billed)') }}</span>
          </div>

          <!-- Non-billable -->
          <div
            v-if="summaryData.totals.non_billable_hours"
            class="flex items-center gap-4 text-[var(--watch-text-muted)]"
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
