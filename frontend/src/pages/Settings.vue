<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Download, ChevronDown } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useUserSettings } from '@/composables/useUserSettings'

// ── Types ─────────────────────────────────────────────────────────────────────

interface WatchSettings {
  default_entry_type:       string
  lock_entries_older_than:  number
  auto_stop_timer_after:    number
  work_mon: 0 | 1
  work_tue: 0 | 1
  work_wed: 0 | 1
  work_thu: 0 | 1
  work_fri: 0 | 1
  work_sat: 0 | 1
  work_sun: 0 | 1
  enable_erpnext_bridge:    0 | 1
  sync_mode:                string
  sync_interval:            string
  erpnext_site_url:         string
  default_activity_type:    string
  sync_billable_only:       0 | 1
  map_project_tags:         0 | 1
  slack_webhook_url:        string
  slack_notify_on_stop:     0 | 1
  slack_message_template:   string
  linear_api_key:           string
  linear_post_comment:      0 | 1
  github_token:             string
  github_default_repo:      string
  github_post_comment:      0 | 1
}

// ── State ─────────────────────────────────────────────────────────────────────

const loading = ref(true)
const saving  = ref(false)
const apiError = ref<string | null>(null)
const saved   = ref(false)

// ── My Preferences (per-user Watch User Settings) ───────────────────────────

const {
  prefs, load: loadPrefs, save: savePrefs,
  generateExtensionToken, revokeExtensionToken,
} = useUserSettings()

const prefsSaving = ref(false)
const prefsSaved  = ref(false)
const prefsError  = ref<string | null>(null)

// ── Browser Extension token ──────────────────────────────────────────────────

const extGenerating = ref(false)
const extRevoking   = ref(false)
const extToken      = ref<string | null>(null)
const extError      = ref<string | null>(null)
const extCopied     = ref(false)

async function handleGenerateToken() {
  if (prefs.value.extension_token_active) {
    if (!window.confirm(__('This will revoke the existing token. Continue?'))) {
      return
    }
  }
  extGenerating.value = true
  extError.value      = null
  extToken.value      = null
  try {
    const token = await generateExtensionToken()
    extToken.value = token
  } catch (e: any) {
    extError.value = e.message
  } finally {
    extGenerating.value = false
  }
}

async function handleRevokeToken() {
  extRevoking.value = true
  extError.value    = null
  extToken.value    = null
  try {
    await revokeExtensionToken()
  } catch (e: any) {
    extError.value = e.message
  } finally {
    extRevoking.value = false
  }
}

async function copyToken() {
  if (!extToken.value) return
  try {
    await navigator.clipboard.writeText(extToken.value)
    extCopied.value = true
    setTimeout(() => { extCopied.value = false }, 2000)
  } catch {
    /* fallback: select the input */
  }
}

async function handleSavePrefs() {
  prefsSaving.value = true
  prefsError.value  = null
  prefsSaved.value  = false
  try {
    await savePrefs({
      weekly_hour_target: prefs.value.weekly_hour_target,
      enable_keyboard_shortcuts: prefs.value.enable_keyboard_shortcuts,
      focus_work_minutes: prefs.value.focus_work_minutes,
      focus_break_minutes: prefs.value.focus_break_minutes,
      focus_sessions: prefs.value.focus_sessions,
    })
    prefsSaved.value = true
    setTimeout(() => { prefsSaved.value = false }, 2500)
  } catch (e: any) {
    prefsError.value = e.message
  } finally {
    prefsSaving.value = false
  }
}

const form = ref<WatchSettings>({
  default_entry_type:      'billable',
  lock_entries_older_than: 0,
  auto_stop_timer_after:   8,
  work_mon: 1, work_tue: 1, work_wed: 1, work_thu: 1, work_fri: 1,
  work_sat: 0, work_sun: 0,
  enable_erpnext_bridge:   0,
  sync_mode:               'on_save',
  sync_interval:           '',
  erpnext_site_url:        '',
  default_activity_type:   '',
  sync_billable_only:      0,
  map_project_tags:        0,
  slack_webhook_url:       '',
  slack_notify_on_stop:    1,
  slack_message_template:  '',
  linear_api_key:          '',
  linear_post_comment:     0,
  github_token:            '',
  github_default_repo:     '',
  github_post_comment:     0,
})

// ── Load ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  const [, prefsResult] = await Promise.allSettled([
    (async () => {
      try {
        const res  = await fetch('/api/method/watch.api.settings.get_settings', {
          headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
        })
        const data = await res.json()
        if (!res.ok || data.exc) throw new Error(data.exc ?? 'Load failed')
        Object.assign(form.value, data.message)
      } catch (e: any) {
        apiError.value = e.message
      } finally {
        loading.value = false
      }
    })(),
    loadPrefs(),
  ])
  if (prefsResult.status === 'rejected') {
    prefsError.value = prefsResult.reason?.message ?? 'Failed to load preferences'
  }
})

// ── Save ──────────────────────────────────────────────────────────────────────

async function handleSave() {
  saving.value   = true
  apiError.value = null
  saved.value    = false
  try {
    const res  = await fetch('/api/method/watch.api.settings.save_settings', {
      method:  'POST',
      headers: {
        'Content-Type':       'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
      body: JSON.stringify(form.value),
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Save failed')
    Object.assign(form.value, data.message)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch (e: any) {
    apiError.value = e.message
  } finally {
    saving.value = false
  }
}

// ── Integration tests ─────────────────────────────────────────────────────────

const slackTesting  = ref(false)
const slackStatus   = ref<string | null>(null)
const linearTesting = ref(false)
const linearStatus  = ref<string | null>(null)
const githubTesting = ref(false)
const githubStatus  = ref<string | null>(null)

async function testIntegration(
  endpoint: string,
  testing: typeof slackTesting,
  status: typeof slackStatus,
  successFn: (msg: any) => string,
) {
  testing.value = true
  status.value  = null
  try {
    const res = await fetch(`/api/method/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data._server_messages || data.exc || 'Test failed')
    status.value = successFn(data.message)
  } catch (e: any) {
    status.value = `Error: ${e.message}`
  } finally {
    testing.value = false
  }
}

function testSlack() {
  testIntegration('watch.api.integrations.test_slack', slackTesting, slackStatus, () => __('Connected'))
}
function testLinear() {
  testIntegration('watch.api.integrations.test_linear', linearTesting, linearStatus,
    (msg) => __('Connected') + (msg?.workspace ? ` (${msg.workspace})` : ''))
}
function testGitHub() {
  testIntegration('watch.api.integrations.test_github', githubTesting, githubStatus,
    (msg) => __('Connected') + (msg?.username ? ` (${msg.username})` : ''))
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const ENTRY_TYPE_OPTIONS = [
  { value: 'billable',     label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal',     label: 'Internal' },
]

const SYNC_MODE_OPTIONS = [
  { value: 'on_save',   label: 'On save' },
  { value: 'manual',    label: 'Manual' },
  { value: 'scheduled', label: 'Scheduled' },
]

const SYNC_INTERVAL_OPTIONS = [
  { value: 'hourly',        label: 'Hourly' },
  { value: 'every_6_hours', label: 'Every 6 hours' },
  { value: 'daily',         label: 'Daily' },
]

const WORK_DAYS: { key: keyof WatchSettings; label: string }[] = [
  { key: 'work_mon', label: 'Mon' },
  { key: 'work_tue', label: 'Tue' },
  { key: 'work_wed', label: 'Wed' },
  { key: 'work_thu', label: 'Thu' },
  { key: 'work_fri', label: 'Fri' },
  { key: 'work_sat', label: 'Sat' },
  { key: 'work_sun', label: 'Sun' },
]

function toggleWorkDay(key: keyof WatchSettings, checked: boolean) {
  (form.value[key] as 0 | 1) = checked ? 1 : 0
}

function toggleCheck(key: keyof WatchSettings, checked: boolean) {
  (form.value[key] as 0 | 1) = checked ? 1 : 0
}

// ── Export my data ────────────────────────────────────────────────────────────

type ExportPreset = 'all_time' | 'this_year' | 'last_year' | 'custom'

const EXPORT_PRESETS: { value: ExportPreset; label: string }[] = [
  { value: 'all_time',   label: 'All time' },
  { value: 'this_year',  label: 'This year' },
  { value: 'last_year',  label: 'Last year' },
  { value: 'custom',     label: 'Custom…' },
]

const exportPreset    = ref<ExportPreset>('all_time')
const exportFromDate  = ref('')
const exportToDate    = ref('')
const exportPresetOpen = ref(false)

const exportPresetLabel = computed(
  () => EXPORT_PRESETS.find(p => p.value === exportPreset.value)?.label ?? __('All time'),
)

function downloadMyData() {
  const now = new Date()
  const today = now.toISOString().slice(0, 10)
  let from_date: string
  let to_date = today

  switch (exportPreset.value) {
    case 'this_year':
      from_date = `${now.getFullYear()}-01-01`
      break
    case 'last_year': {
      const yr = now.getFullYear() - 1
      from_date = `${yr}-01-01`
      to_date   = `${yr}-12-31`
      break
    }
    case 'custom':
      from_date = exportFromDate.value
      to_date   = exportToDate.value
      break
    default: // all_time
      from_date = '2000-01-01'
  }

  const params = new URLSearchParams({ from_date, to_date })
  window.location.href = `/api/method/watch.api.time_entry.export_csv?${params}`
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-slate-800">
    <div class="max-w-2xl mx-auto px-4 py-6 space-y-4">

      <!-- Heading -->
      <h1 class="text-lg font-semibold text-gray-900 dark:text-slate-100">{{ __('Settings') }}</h1>

      <!-- Loading skeleton -->
      <template v-if="loading">
        <div
          v-for="i in 4" :key="i"
          class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 p-4 animate-pulse h-14"
        />
      </template>

      <!-- Load error -->
      <p v-else-if="apiError && !form" class="text-sm text-red-500 px-1">{{ apiError }}</p>

      <template v-else>

        <!-- ── My Preferences (per-user) ──────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('My Preferences') }}</h2>
            <p class="text-xs text-gray-500 dark:text-slate-500 mt-0.5">{{ __('Personal settings — only you can see these.') }}</p>
          </div>

          <!-- Weekly hour target -->
          <div class="px-4 py-3 flex items-center gap-4">
            <div class="flex-1">
              <div class="text-sm text-gray-900 dark:text-slate-100">{{ __('Weekly hour target') }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-500">{{ __('0 = no target (progress bar hidden).') }}</div>
            </div>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="prefs.weekly_hour_target"
                type="number"
                min="0"
                step="1"
                class="w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
              <span class="text-xs text-gray-500 dark:text-slate-500">{{ __('hours') }}</span>
            </div>
          </div>

          <!-- Keyboard shortcuts -->
          <div class="px-4 py-3 flex items-center gap-4">
            <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Keyboard shortcuts') }}</label>
            <label class="flex items-center gap-2 cursor-pointer shrink-0">
              <input
                type="checkbox"
                :checked="!!prefs.enable_keyboard_shortcuts"
                class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                @change="prefs.enable_keyboard_shortcuts = ($event.target as HTMLInputElement).checked ? 1 : 0"
              />
              <span class="text-sm text-gray-900 dark:text-slate-100">{{ __('Enabled') }}</span>
            </label>
          </div>

          <!-- Save prefs -->
          <div class="px-4 py-3 flex items-center gap-3 justify-end">
            <p v-if="prefsError" class="text-xs text-red-500 flex-1">{{ prefsError }}</p>
            <p v-if="prefsSaved" class="text-xs text-green-600 dark:text-green-400 flex-1">{{ __('Saved.') }}</p>
            <button
              type="button"
              :disabled="prefsSaving"
              class="px-4 py-1.5 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                     text-white text-sm font-medium transition-colors disabled:opacity-50"
              @click="handleSavePrefs"
            >
              {{ prefsSaving ? __('Saving…') : __('Save') }}
            </button>
          </div>
        </div>

        <!-- ── Browser Extension ──────────────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('Browser Extension') }}</h2>
            <p class="text-xs text-gray-500 dark:text-slate-500 mt-0.5">{{ __('Connect the Watch browser extension to this site.') }}</p>
          </div>

          <div class="px-4 py-3 space-y-3">
            <!-- Status -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500 dark:text-slate-500">{{ __('Status') }}:</span>
              <span
                class="text-sm font-medium"
                :class="prefs.extension_token_active ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-slate-500'"
              >
                {{ prefs.extension_token_active ? __('Token active') : __('Not connected') }}
              </span>
            </div>

            <!-- Token display (shown once after generation) -->
            <div v-if="extToken" class="space-y-2">
              <div class="flex items-center gap-2">
                <input
                  type="text"
                  :value="extToken"
                  readonly
                  class="flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800
                         text-xs font-mono text-gray-900 dark:text-slate-100 outline-none select-all"
                  @focus="($event.target as HTMLInputElement).select()"
                />
                <button
                  type="button"
                  class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium
                         text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                  @click="copyToken"
                >
                  {{ extCopied ? __('Copied') : __('Copy') }}
                </button>
              </div>
              <p class="text-xs text-amber-600 dark:text-amber-400">
                {{ __('This token will not be shown again. Paste it into the extension setup screen.') }}
              </p>
            </div>

            <!-- Error -->
            <p v-if="extError" class="text-xs text-red-500">{{ extError }}</p>

            <!-- Actions -->
            <div class="flex items-center gap-2">
              <button
                v-if="!prefs.extension_token_active"
                type="button"
                :disabled="extGenerating"
                class="px-4 py-1.5 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                       text-white text-sm font-medium transition-colors disabled:opacity-50"
                @click="handleGenerateToken"
              >
                {{ extGenerating ? __('Generating…') : __('Generate extension token') }}
              </button>

              <template v-else>
                <button
                  type="button"
                  :disabled="extGenerating"
                  class="px-4 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                         text-sm font-medium text-gray-900 dark:text-slate-100
                         hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
                  @click="handleGenerateToken"
                >
                  {{ extGenerating ? __('Generating…') : __('Regenerate token') }}
                </button>
                <button
                  type="button"
                  :disabled="extRevoking"
                  class="px-4 py-1.5 rounded-lg border border-red-300 dark:border-red-700
                         text-sm font-medium text-red-600 dark:text-red-400
                         hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                  @click="handleRevokeToken"
                >
                  {{ extRevoking ? __('Revoking…') : __('Revoke access') }}
                </button>
              </template>
            </div>
          </div>
        </div>

        <!-- ── General ────────────────────────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('General') }}</h2>
          </div>

          <!-- Default entry type -->
          <div class="px-4 py-3 flex items-center gap-4">
            <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Default entry type') }}</label>
            <select
              v-model="form.default_entry_type"
              class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                     text-sm text-gray-900 dark:text-slate-100 outline-none
                     focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
            >
              <option v-for="opt in ENTRY_TYPE_OPTIONS" :key="opt.value" :value="opt.value">
                {{ __(opt.label) }}
              </option>
            </select>
          </div>

          <!-- Lock entries -->
          <div class="px-4 py-3 flex items-center gap-4">
            <div class="flex-1">
              <div class="text-sm text-gray-900 dark:text-slate-100">{{ __('Lock entries older than (days)') }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-500">{{ __('0 = disabled.') }}</div>
            </div>
            <input
              v-model.number="form.lock_entries_older_than"
              type="number"
              min="0"
              class="w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                     text-sm text-gray-900 dark:text-slate-100 outline-none
                     focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
            />
          </div>

          <!-- Auto-stop -->
          <div class="px-4 py-3 flex items-center gap-4">
            <div class="flex-1">
              <div class="text-sm text-gray-900 dark:text-slate-100">{{ __('Auto-stop timer after (hours)') }}</div>
              <div class="text-xs text-gray-500 dark:text-slate-500">{{ __('0 = disabled.') }}</div>
            </div>
            <input
              v-model.number="form.auto_stop_timer_after"
              type="number"
              min="0"
              class="w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                     text-sm text-gray-900 dark:text-slate-100 outline-none
                     focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
            />
          </div>

          <!-- Work days — horizontal checkbox row -->
          <div class="px-4 py-3 space-y-2">
            <div class="text-sm text-gray-900 dark:text-slate-100">{{ __('Work days') }}</div>
            <div class="flex gap-4">
              <label
                v-for="day in WORK_DAYS"
                :key="day.key"
                class="flex flex-col items-center gap-1 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="!!form[day.key]"
                  class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                  @change="toggleWorkDay(day.key, ($event.target as HTMLInputElement).checked)"
                />
                <span class="text-xs text-gray-500 dark:text-slate-500 select-none">{{ __(day.label) }}</span>
              </label>
            </div>
          </div>

        </div>

        <!-- ── ERPNext Bridge ─────────────────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3 flex items-center gap-4">
            <div class="flex-1">
              <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('ERPNext Bridge') }}</h2>
              <p class="text-xs text-gray-500 dark:text-slate-500">{{ __('One-way sync of billable entries to ERPNext Timesheets.') }}</p>
            </div>
            <label class="flex items-center gap-2 cursor-pointer shrink-0">
              <input
                type="checkbox"
                :checked="!!form.enable_erpnext_bridge"
                class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                @change="toggleCheck('enable_erpnext_bridge', ($event.target as HTMLInputElement).checked)"
              />
              <span class="text-sm text-gray-900 dark:text-slate-100">{{ __('Enable') }}</span>
            </label>
          </div>

          <template v-if="form.enable_erpnext_bridge">
            <!-- ERPNext site URL -->
            <div class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('ERPNext site URL') }}</label>
              <input
                v-model="form.erpnext_site_url"
                type="url"
                placeholder="https://erp.example.com"
                class="w-56 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
            </div>

            <!-- Sync mode -->
            <div class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Sync mode') }}</label>
              <select
                v-model="form.sync_mode"
                class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              >
                <option v-for="opt in SYNC_MODE_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ __(opt.label) }}
                </option>
              </select>
            </div>

            <!-- Sync interval (scheduled only) -->
            <div v-if="form.sync_mode === 'scheduled'" class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Sync interval') }}</label>
              <select
                v-model="form.sync_interval"
                class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              >
                <option v-for="opt in SYNC_INTERVAL_OPTIONS" :key="opt.value" :value="opt.value">
                  {{ __(opt.label) }}
                </option>
              </select>
            </div>

            <!-- Default activity type -->
            <div class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Default activity type') }}</label>
              <input
                v-model="form.default_activity_type"
                type="text"
                class="w-40 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
            </div>

            <!-- Sync billable only -->
            <div class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Sync billable entries only') }}</label>
              <input
                type="checkbox"
                :checked="!!form.sync_billable_only"
                class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                @change="toggleCheck('sync_billable_only', ($event.target as HTMLInputElement).checked)"
              />
            </div>

            <!-- Map project tags -->
            <div class="px-4 py-3 flex items-center gap-4">
              <label class="text-sm text-gray-900 dark:text-slate-100 flex-1">{{ __('Map project tags to ERPNext projects') }}</label>
              <input
                type="checkbox"
                :checked="!!form.map_project_tags"
                class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                @change="toggleCheck('map_project_tags', ($event.target as HTMLInputElement).checked)"
              />
            </div>
          </template>
        </div>

        <!-- ── Integrations ────────────────────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('Integrations') }}</h2>
            <p class="text-xs text-gray-500 dark:text-slate-500 mt-0.5">{{ __('Connect Watch to Slack, Linear, and GitHub.') }}</p>
          </div>

          <!-- Slack -->
          <div class="px-4 py-3 space-y-3">
            <div class="text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide">{{ __('Slack') }}</div>

            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0">{{ __('Webhook URL') }}</label>
              <input
                v-model="form.slack_webhook_url"
                type="password"
                placeholder="https://hooks.slack.com/..."
                class="flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
              <button
                type="button"
                :disabled="slackTesting || !form.slack_webhook_url"
                class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium
                       text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors
                       disabled:opacity-40"
                @click="testSlack"
              >
                {{ slackTesting ? __('Testing…') : __('Test') }}
              </button>
            </div>

            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="!!form.slack_notify_on_stop"
                  class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                  @change="toggleCheck('slack_notify_on_stop', ($event.target as HTMLInputElement).checked)"
                />
                <span class="text-sm text-gray-900 dark:text-slate-100">{{ __('Notify on timer stop') }}</span>
              </label>
            </div>

            <div class="flex flex-col gap-1">
              <label class="text-xs text-gray-500 dark:text-slate-500">{{ __('Message template (optional)') }}</label>
              <input
                v-model="form.slack_message_template"
                type="text"
                :placeholder="'⏱ {description} — {duration} logged{tag_part}'"
                class="px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
            </div>

            <p
              v-if="slackStatus"
              class="text-xs"
              :class="slackStatus.startsWith('Error') ? 'text-red-500' : 'text-green-600 dark:text-green-400'"
            >
              {{ slackStatus }}
            </p>
          </div>

          <!-- Linear -->
          <div class="px-4 py-3 space-y-3">
            <div class="text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide">{{ __('Linear') }}</div>

            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0">{{ __('API Key') }}</label>
              <input
                v-model="form.linear_api_key"
                type="password"
                placeholder="lin_api_…"
                class="flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
              <button
                type="button"
                :disabled="linearTesting || !form.linear_api_key"
                class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium
                       text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors
                       disabled:opacity-40"
                @click="testLinear"
              >
                {{ linearTesting ? __('Testing…') : __('Test') }}
              </button>
            </div>

            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="!!form.linear_post_comment"
                  class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                  @change="toggleCheck('linear_post_comment', ($event.target as HTMLInputElement).checked)"
                />
                <span class="text-sm text-gray-900 dark:text-slate-100">{{ __('Post comment on save') }}</span>
              </label>
            </div>

            <p
              v-if="linearStatus"
              class="text-xs"
              :class="linearStatus.startsWith('Error') ? 'text-red-500' : 'text-green-600 dark:text-green-400'"
            >
              {{ linearStatus }}
            </p>
          </div>

          <!-- GitHub -->
          <div class="px-4 py-3 space-y-3">
            <div class="text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide">{{ __('GitHub') }}</div>

            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0">{{ __('Token') }}</label>
              <input
                v-model="form.github_token"
                type="password"
                placeholder="ghp_…"
                class="flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
              <button
                type="button"
                :disabled="githubTesting || !form.github_token"
                class="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium
                       text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors
                       disabled:opacity-40"
                @click="testGitHub"
              >
                {{ githubTesting ? __('Testing…') : __('Test') }}
              </button>
            </div>

            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0">{{ __('Default repo') }}</label>
              <input
                v-model="form.github_default_repo"
                type="text"
                placeholder="owner/repo"
                class="flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950
                       text-sm text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
            </div>

            <div class="flex items-center gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  :checked="!!form.github_post_comment"
                  class="w-4 h-4 rounded accent-[var(--app-accent-500)]"
                  @change="toggleCheck('github_post_comment', ($event.target as HTMLInputElement).checked)"
                />
                <span class="text-sm text-gray-900 dark:text-slate-100">{{ __('Post comment on save') }}</span>
              </label>
            </div>

            <p
              v-if="githubStatus"
              class="text-xs"
              :class="githubStatus.startsWith('Error') ? 'text-red-500' : 'text-green-600 dark:text-green-400'"
            >
              {{ githubStatus }}
            </p>
          </div>
        </div>

        <!-- ── Export my data ─────────────────────────────────────── -->
        <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
          <div class="px-4 py-3">
            <h2 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('Export my data') }}</h2>
            <p class="text-xs text-gray-500 dark:text-slate-500 mt-0.5">{{ __('Download all your time entries as CSV.') }}</p>
          </div>

          <div class="px-4 py-3 flex flex-wrap items-center gap-2">
            <!-- Preset dropdown -->
            <div class="relative">
              <button
                type="button"
                class="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                       text-sm text-gray-900 dark:text-slate-100 hover:border-[var(--app-accent-500)]/50 transition-colors"
                @click="exportPresetOpen = !exportPresetOpen"
              >
                {{ __(exportPresetLabel) }}
                <ChevronDown class="w-3.5 h-3.5" aria-hidden="true" />
              </button>
              <div
                v-if="exportPresetOpen"
                class="absolute left-0 top-full mt-1 z-20 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700
                       rounded-xl shadow-lg py-1 min-w-[140px]"
              >
                <button
                  v-for="p in EXPORT_PRESETS"
                  :key="p.value"
                  type="button"
                  :class="[
                    'w-full text-left px-3 py-1.5 text-sm transition-colors',
                    exportPreset === p.value
                      ? 'text-[var(--app-accent-500)] font-medium'
                      : 'text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800',
                  ]"
                  @click="exportPreset = p.value; exportPresetOpen = false"
                >
                  {{ __(p.label) }}
                </button>
              </div>
            </div>

            <!-- Custom date pickers -->
            <template v-if="exportPreset === 'custom'">
              <input
                v-model="exportFromDate"
                type="date"
                :max="exportToDate || undefined"
                class="px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                       bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
              <span class="text-gray-500 dark:text-slate-500 text-sm">→</span>
              <input
                v-model="exportToDate"
                type="date"
                :min="exportFromDate || undefined"
                class="px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700
                       bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none
                       focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              />
            </template>

            <button
              type="button"
              :disabled="exportPreset === 'custom' && (!exportFromDate || !exportToDate)"
              class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700
                     text-sm text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800
                     transition-colors disabled:opacity-40"
              @click="downloadMyData"
            >
              <Download class="w-3.5 h-3.5" aria-hidden="true" />
              {{ __('Download CSV') }}
            </button>
          </div>
        </div>

        <!-- Error / success -->
        <p v-if="apiError" class="text-sm text-red-500 px-1">{{ apiError }}</p>
        <p v-if="saved" class="text-sm text-green-600 dark:text-green-400 px-1">{{ __('Settings saved.') }}</p>

        <!-- Save button -->
        <div class="flex justify-end">
          <button
            type="button"
            :disabled="saving"
            class="px-5 py-2 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)]
                   text-white text-sm font-medium transition-colors disabled:opacity-50"
            @click="handleSave"
          >
            {{ saving ? __('Saving…') : __('Save settings') }}
          </button>
        </div>

      </template>
    </div>
  </div>
</template>
