<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic

  Watch Settings — rendered inside Dock's unified settings host.
  Dock provides the page title ("Watch Settings") and layout chrome.
-->
<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { Download } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

// ── Types ──────────────────────────────────────────────────────

interface WatchSettings {
  default_entry_type: string
  lock_entries_older_than: number
  auto_stop_timer_after: number
  work_mon: 0 | 1
  work_tue: 0 | 1
  work_wed: 0 | 1
  work_thu: 0 | 1
  work_fri: 0 | 1
  work_sat: 0 | 1
  work_sun: 0 | 1
  enable_erpnext_bridge: 0 | 1
  erpnext_site_url: string
  sync_mode: string
  sync_interval: string
  default_activity_type: string
  sync_billable_only: 0 | 1
  map_project_tags: 0 | 1
  slack_webhook_url: string
  slack_notify_on_stop: 0 | 1
  slack_message_template: string
  linear_api_key: string
  linear_post_comment: 0 | 1
  github_token: string
  github_default_repo: string
  github_post_comment: 0 | 1
  [key: string]: unknown
}

interface UserPrefs {
  weekly_hour_target: number
  enable_keyboard_shortcuts: 0 | 1
  extension_token_active: boolean
}

// ── Constants ──────────────────────────────────────────────────

const ENTRY_TYPE_OPTIONS = [
  { value: 'billable', label: 'Billable' },
  { value: 'non-billable', label: 'Non-billable' },
  { value: 'internal', label: 'Internal' },
]

const SYNC_MODE_OPTIONS = [
  { value: 'on_save', label: 'On save' },
  { value: 'manual', label: 'Manual' },
  { value: 'scheduled', label: 'Scheduled' },
]

const SYNC_INTERVAL_OPTIONS = [
  { value: 'hourly', label: 'Hourly' },
  { value: 'every_6_hours', label: 'Every 6 hours' },
  { value: 'daily', label: 'Daily' },
]

const WORK_DAYS = [
  { key: 'work_mon', label: 'Mon' },
  { key: 'work_tue', label: 'Tue' },
  { key: 'work_wed', label: 'Wed' },
  { key: 'work_thu', label: 'Thu' },
  { key: 'work_fri', label: 'Fri' },
  { key: 'work_sat', label: 'Sat' },
  { key: 'work_sun', label: 'Sun' },
] as const

const EXPORT_PRESETS = [
  { value: 'all', label: 'All time' },
  { value: 'this_year', label: 'This year' },
  { value: 'last_year', label: 'Last year' },
  { value: 'custom', label: 'Custom range' },
]

// ── Tabs ───────────────────────────────────────────────────────

const tabs = [
  { label: __('My Preferences') },
  { label: __('General') },
  { label: __('ERPNext Bridge') },
  { label: __('Integrations') },
  { label: __('Export') },
]

const activeTab = ref(0)

// ── State ──────────────────────────────────────────────────────

const loading = ref(true)
const saving = ref(false)
const saved = ref(false)
const apiError = ref('')

const prefsSaving = ref(false)
const prefsSaved = ref(false)
const prefsError = ref('')

const form = reactive<WatchSettings>({
  default_entry_type: 'billable',
  lock_entries_older_than: 0,
  auto_stop_timer_after: 0,
  work_mon: 1, work_tue: 1, work_wed: 1, work_thu: 1, work_fri: 1, work_sat: 0, work_sun: 0,
  enable_erpnext_bridge: 0,
  erpnext_site_url: '',
  sync_mode: 'on_save',
  sync_interval: 'daily',
  default_activity_type: '',
  sync_billable_only: 0,
  map_project_tags: 0,
  slack_webhook_url: '',
  slack_notify_on_stop: 0,
  slack_message_template: '',
  linear_api_key: '',
  linear_post_comment: 0,
  github_token: '',
  github_default_repo: '',
  github_post_comment: 0,
})

const prefs = reactive<UserPrefs>({
  weekly_hour_target: 0,
  enable_keyboard_shortcuts: 1,
  extension_token_active: false,
})

// Browser extension state
const extToken = ref('')
const extCopied = ref(false)
const extGenerating = ref(false)
const extRevoking = ref(false)
const extError = ref('')

// Integration test state
const slackTesting = ref(false)
const slackTestResult = ref<{ ok: boolean; msg: string } | null>(null)
const linearTesting = ref(false)
const linearTestResult = ref<{ ok: boolean; msg: string } | null>(null)
const githubTesting = ref(false)
const githubTestResult = ref<{ ok: boolean; msg: string } | null>(null)

// Export state
const exportPreset = ref('all')
const exportFromDate = ref('')
const exportToDate = ref('')
const exportPresetOpen = ref(false)

// ── Frappe API helpers ─────────────────────────────────────────

async function callApi(method: string, args: Record<string, unknown> = {}) {
  return (window as any).frappe.call({ method, args, type: 'POST' })
}

// ── Load ───────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [settingsRes, prefsRes] = await Promise.all([
      callApi('frappe.client.get', { doctype: 'Watch Settings', name: 'Watch Settings' }),
      callApi('watch.api.settings.get_user_preferences'),
    ])
    const s = settingsRes.message
    if (s) {
      Object.keys(form).forEach(k => { if (s[k] !== undefined) (form as any)[k] = s[k] })
    }
    const p = prefsRes.message
    if (p) {
      prefs.weekly_hour_target = p.weekly_hour_target ?? 0
      prefs.enable_keyboard_shortcuts = p.enable_keyboard_shortcuts ?? 1
      prefs.extension_token_active = !!p.extension_token_active
    }
  } catch (e: any) {
    apiError.value = e?.message || __('Failed to load settings')
  } finally {
    loading.value = false
  }
})

// ── Preferences save ───────────────────────────────────────────

async function handleSavePrefs() {
  prefsSaving.value = true
  prefsError.value = ''
  prefsSaved.value = false
  try {
    await callApi('watch.api.settings.save_user_preferences', {
      weekly_hour_target: prefs.weekly_hour_target,
      enable_keyboard_shortcuts: prefs.enable_keyboard_shortcuts,
    })
    prefsSaved.value = true
    setTimeout(() => (prefsSaved.value = false), 2500)
  } catch (e: any) {
    prefsError.value = e?.message || __('Failed to save')
  } finally {
    prefsSaving.value = false
  }
}

// ── General save ───────────────────────────────────────────────

async function handleSave() {
  saving.value = true
  apiError.value = ''
  saved.value = false
  try {
    await callApi('frappe.client.set_value', {
      doctype: 'Watch Settings',
      name: 'Watch Settings',
      fieldname: { ...form },
    })
    saved.value = true
    setTimeout(() => (saved.value = false), 2500)
  } catch (e: any) {
    apiError.value = e?.message || __('Failed to save')
  } finally {
    saving.value = false
  }
}

// ── Browser extension ──────────────────────────────────────────

async function handleGenerateToken() {
  extGenerating.value = true
  extError.value = ''
  extToken.value = ''
  try {
    const res = await callApi('watch.api.settings.generate_extension_token')
    extToken.value = res.message?.token ?? ''
    prefs.extension_token_active = true
  } catch (e: any) {
    extError.value = e?.message || __('Failed to generate token')
  } finally {
    extGenerating.value = false
  }
}

async function handleRevokeToken() {
  if (!confirm(__('Revoke the browser extension token? The extension will be disconnected.'))) return
  extRevoking.value = true
  extError.value = ''
  try {
    await callApi('watch.api.settings.revoke_extension_token')
    prefs.extension_token_active = false
    extToken.value = ''
  } catch (e: any) {
    extError.value = e?.message || __('Failed to revoke token')
  } finally {
    extRevoking.value = false
  }
}

function copyToken() {
  navigator.clipboard.writeText(extToken.value)
  extCopied.value = true
  setTimeout(() => (extCopied.value = false), 2000)
}

// ── Integration tests ──────────────────────────────────────────

async function testIntegration(
  name: string,
  testing: typeof slackTesting,
  result: typeof slackTestResult,
) {
  testing.value = true
  result.value = null
  try {
    const res = await callApi(`watch.api.integrations.test_${name}`)
    result.value = { ok: res.message?.success ?? false, msg: res.message?.message ?? '' }
  } catch (e: any) {
    result.value = { ok: false, msg: e?.message || __('Test failed') }
  } finally {
    testing.value = false
  }
}

function testSlack() { testIntegration('slack', slackTesting, slackTestResult) }
function testLinear() { testIntegration('linear', linearTesting, linearTestResult) }
function testGitHub() { testIntegration('github', githubTesting, githubTestResult) }

// ── Work day toggle ────────────────────────────────────────────

function toggleWorkDay(key: string, checked: boolean) {
  ;(form as any)[key] = checked ? 1 : 0
}

function toggleCheck(key: string, checked: boolean) {
  ;(form as any)[key] = checked ? 1 : 0
}

// ── Export ──────────────────────────────────────────────────────

async function downloadMyData() {
  let from = ''
  let to = ''
  const now = new Date()

  if (exportPreset.value === 'this_year') {
    from = `${now.getFullYear()}-01-01`
    to = now.toISOString().slice(0, 10)
  } else if (exportPreset.value === 'last_year') {
    from = `${now.getFullYear() - 1}-01-01`
    to = `${now.getFullYear() - 1}-12-31`
  } else if (exportPreset.value === 'custom') {
    from = exportFromDate.value
    to = exportToDate.value
  }

  window.open(
    `/api/method/watch.api.export.download_csv?from_date=${from}&to_date=${to}`,
    '_blank',
  )
}
</script>

<template>
  <!-- Loading -->
  <div v-if="loading" class="flex items-center justify-center py-20">
    <div class="h-6 w-6 animate-spin rounded-full border-2 border-accent-600 border-t-transparent" />
  </div>

  <!-- Error -->
  <p v-else-if="apiError && !form" class="text-sm text-red-500">{{ apiError }}</p>

  <template v-else>
    <!-- Tab bar -->
    <nav class="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6">
      <button
        v-for="(tab, i) in tabs"
        :key="tab.label"
        class="relative px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === i
          ? 'text-gray-900 dark:text-white'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
        @click="activeTab = i"
      >
        {{ tab.label }}
        <span
          v-if="activeTab === i"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-600 dark:bg-accent-400 rounded-full"
        />
      </button>
    </nav>

    <!-- ── My Preferences ──────────────────────────────────────── -->
    <div v-if="activeTab === 0" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Personal Settings') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Only you can see these.') }}</p>
        <div class="space-y-5">
          <!-- Weekly hour target -->
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Weekly hour target') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('0 = no target (progress bar hidden).') }}</p>
            </div>
            <div class="flex items-center gap-1.5">
              <input
                v-model.number="prefs.weekly_hour_target"
                type="number" min="0" step="1"
                class="w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                       px-3 py-2 text-sm text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              />
              <span class="text-xs text-gray-400 dark:text-gray-500">{{ __('hours') }}</span>
            </div>
          </div>

          <!-- Keyboard shortcuts -->
          <div class="flex items-center gap-4">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 flex-1">{{ __('Keyboard shortcuts') }}</label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                :checked="!!prefs.enable_keyboard_shortcuts"
                class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
                @change="prefs.enable_keyboard_shortcuts = ($event.target as HTMLInputElement).checked ? 1 : 0"
              />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Enabled') }}</span>
            </label>
          </div>
        </div>

        <!-- Save prefs -->
        <div class="flex items-center gap-3 mt-5 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button
            :disabled="prefsSaving"
            class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
                   hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
            @click="handleSavePrefs"
          >
            {{ prefsSaving ? __('Saving…') : __('Save') }}
          </button>
          <span v-if="prefsSaved" class="text-xs text-green-600 dark:text-green-400">{{ __('Saved') }}</span>
          <span v-if="prefsError" class="text-xs text-red-500">{{ prefsError }}</span>
        </div>
      </div>

      <!-- Browser Extension -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Browser Extension') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Connect the Watch browser extension to this site.') }}</p>

        <div class="space-y-4">
          <!-- Status -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ __('Status') }}:</span>
            <span
              class="text-sm font-medium"
              :class="prefs.extension_token_active ? 'text-green-600 dark:text-green-400' : 'text-gray-400 dark:text-gray-500'"
            >
              {{ prefs.extension_token_active ? __('Token active') : __('Not connected') }}
            </span>
          </div>

          <!-- Token display -->
          <div v-if="extToken" class="space-y-2">
            <div class="flex items-center gap-2">
              <input
                type="text" :value="extToken" readonly
                class="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900
                       px-3 py-2 text-xs font-mono text-gray-900 dark:text-white select-all"
                @focus="($event.target as HTMLInputElement).select()"
              />
              <button
                class="rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm font-medium
                       text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                @click="copyToken"
              >
                {{ extCopied ? __('Copied') : __('Copy') }}
              </button>
            </div>
            <p class="text-xs text-amber-600 dark:text-amber-400">
              {{ __('This token will not be shown again. Paste it into the extension setup screen.') }}
            </p>
          </div>

          <p v-if="extError" class="text-xs text-red-500">{{ extError }}</p>

          <!-- Actions -->
          <div class="flex items-center gap-2">
            <button
              v-if="!prefs.extension_token_active"
              :disabled="extGenerating"
              class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
                     hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
              @click="handleGenerateToken"
            >
              {{ extGenerating ? __('Generating…') : __('Generate extension token') }}
            </button>
            <template v-else>
              <button
                :disabled="extGenerating"
                class="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
                       text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                @click="handleGenerateToken"
              >
                {{ extGenerating ? __('Generating…') : __('Regenerate token') }}
              </button>
              <button
                :disabled="extRevoking"
                class="rounded-lg border border-red-300 dark:border-red-700 px-4 py-2 text-sm font-medium
                       text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                @click="handleRevokeToken"
              >
                {{ extRevoking ? __('Revoking…') : __('Revoke access') }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ── General ─────────────────────────────────────────────── -->
    <div v-else-if="activeTab === 1" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Time Tracking') }}
        </h2>
        <div class="space-y-5">
          <div class="flex items-center gap-4">
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 flex-1">{{ __('Default entry type') }}</label>
            <select
              v-model="form.default_entry_type"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            >
              <option v-for="opt in ENTRY_TYPE_OPTIONS" :key="opt.value" :value="opt.value">{{ __(opt.label) }}</option>
            </select>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Lock entries older than (days)') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('0 = disabled.') }}</p>
            </div>
            <input
              v-model.number="form.lock_entries_older_than" type="number" min="0"
              class="w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>

          <div class="flex items-center gap-4">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ __('Auto-stop timer after (hours)') }}</label>
              <p class="text-xs text-gray-400 dark:text-gray-500">{{ __('0 = disabled.') }}</p>
            </div>
            <input
              v-model.number="form.auto_stop_timer_after" type="number" min="0"
              class="w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>

          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">{{ __('Work days') }}</label>
            <div class="flex gap-4">
              <label v-for="day in WORK_DAYS" :key="day.key" class="flex flex-col items-center gap-1 cursor-pointer">
                <input
                  type="checkbox" :checked="!!form[day.key]"
                  class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
                  @change="toggleWorkDay(day.key, ($event.target as HTMLInputElement).checked)"
                />
                <span class="text-xs text-gray-400 dark:text-gray-500 select-none">{{ __(day.label) }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4">
        <button
          :disabled="saving"
          class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
                 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
          @click="handleSave"
        >
          {{ saving ? __('Saving…') : __('Save') }}
        </button>
        <span v-if="saved" class="text-xs text-green-600 dark:text-green-400">{{ __('Saved') }}</span>
        <span v-if="apiError" class="text-xs text-red-500">{{ apiError }}</span>
      </div>
    </div>

    <!-- ── ERPNext Bridge ──────────────────────────────────────── -->
    <div v-else-if="activeTab === 2" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ __('ERPNext Bridge') }}</h2>
            <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{{ __('One-way sync of billable entries to ERPNext Timesheets.') }}</p>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox" :checked="!!form.enable_erpnext_bridge"
              class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
              @change="toggleCheck('enable_erpnext_bridge', ($event.target as HTMLInputElement).checked)"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Enable') }}</span>
          </label>
        </div>

        <template v-if="form.enable_erpnext_bridge">
          <div class="space-y-5">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('ERPNext site URL') }}</label>
              <input
                v-model="form.erpnext_site_url" type="url" placeholder="https://erp.example.com"
                class="w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                       px-3 py-2 text-sm text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              />
            </div>

            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Sync mode') }}</label>
                <select
                  v-model="form.sync_mode"
                  class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                         px-3 py-2 text-sm text-gray-900 dark:text-white
                         focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                >
                  <option v-for="opt in SYNC_MODE_OPTIONS" :key="opt.value" :value="opt.value">{{ __(opt.label) }}</option>
                </select>
              </div>

              <div v-if="form.sync_mode === 'scheduled'">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Sync interval') }}</label>
                <select
                  v-model="form.sync_interval"
                  class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                         px-3 py-2 text-sm text-gray-900 dark:text-white
                         focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                >
                  <option v-for="opt in SYNC_INTERVAL_OPTIONS" :key="opt.value" :value="opt.value">{{ __(opt.label) }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Default activity type') }}</label>
              <input
                v-model="form.default_activity_type" type="text" placeholder="Development"
                class="w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                       px-3 py-2 text-sm text-gray-900 dark:text-white
                       focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              />
            </div>

            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" :checked="!!form.sync_billable_only"
                class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
                @change="toggleCheck('sync_billable_only', ($event.target as HTMLInputElement).checked)"
              />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Sync billable entries only') }}</span>
            </label>

            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" :checked="!!form.map_project_tags"
                class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
                @change="toggleCheck('map_project_tags', ($event.target as HTMLInputElement).checked)"
              />
              <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Map project tags to ERPNext') }}</span>
            </label>
          </div>
        </template>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4">
        <button
          :disabled="saving"
          class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
                 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
          @click="handleSave"
        >
          {{ saving ? __('Saving…') : __('Save') }}
        </button>
        <span v-if="saved" class="text-xs text-green-600 dark:text-green-400">{{ __('Saved') }}</span>
        <span v-if="apiError" class="text-xs text-red-500">{{ apiError }}</span>
      </div>
    </div>

    <!-- ── Integrations ────────────────────────────────────────── -->
    <div v-else-if="activeTab === 3" class="max-w-2xl space-y-6">
      <!-- Slack -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ __('Slack') }}</h2>
        <div class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Webhook URL') }}</label>
            <input
              v-model="form.slack_webhook_url" type="url" placeholder="https://hooks.slack.com/services/..."
              class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" :checked="!!form.slack_notify_on_stop"
              class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
              @change="toggleCheck('slack_notify_on_stop', ($event.target as HTMLInputElement).checked)"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Notify when timer stops') }}</span>
          </label>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Message template') }}</label>
            <textarea
              v-model="form.slack_message_template" rows="3"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <div class="flex items-center gap-3">
            <button
              :disabled="slackTesting || !form.slack_webhook_url"
              class="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
                     text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              @click="testSlack"
            >
              {{ slackTesting ? __('Testing…') : __('Test Connection') }}
            </button>
            <span v-if="slackTestResult" class="text-xs" :class="slackTestResult.ok ? 'text-green-600' : 'text-red-500'">
              {{ slackTestResult.msg }}
            </span>
          </div>
        </div>
      </div>

      <!-- Linear -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ __('Linear') }}</h2>
        <div class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('API Key') }}</label>
            <input
              v-model="form.linear_api_key" type="password"
              class="w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" :checked="!!form.linear_post_comment"
              class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
              @change="toggleCheck('linear_post_comment', ($event.target as HTMLInputElement).checked)"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Post time entry as comment on issue') }}</span>
          </label>
          <div class="flex items-center gap-3">
            <button
              :disabled="linearTesting || !form.linear_api_key"
              class="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
                     text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              @click="testLinear"
            >
              {{ linearTesting ? __('Testing…') : __('Test Connection') }}
            </button>
            <span v-if="linearTestResult" class="text-xs" :class="linearTestResult.ok ? 'text-green-600' : 'text-red-500'">
              {{ linearTestResult.msg }}
            </span>
          </div>
        </div>
      </div>

      <!-- GitHub -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ __('GitHub') }}</h2>
        <div class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Personal Access Token') }}</label>
            <input
              v-model="form.github_token" type="password"
              class="w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Default repository') }}</label>
            <input
              v-model="form.github_default_repo" type="text" placeholder="owner/repo"
              class="w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" :checked="!!form.github_post_comment"
              class="h-4 w-4 rounded accent-accent-600 dark:accent-accent-400"
              @change="toggleCheck('github_post_comment', ($event.target as HTMLInputElement).checked)"
            />
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ __('Post time entry as comment on issue') }}</span>
          </label>
          <div class="flex items-center gap-3">
            <button
              :disabled="githubTesting || !form.github_token"
              class="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
                     text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
              @click="testGitHub"
            >
              {{ githubTesting ? __('Testing…') : __('Test Connection') }}
            </button>
            <span v-if="githubTestResult" class="text-xs" :class="githubTestResult.ok ? 'text-green-600' : 'text-red-500'">
              {{ githubTestResult.msg }}
            </span>
          </div>
        </div>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4">
        <button
          :disabled="saving"
          class="rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900
                 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50"
          @click="handleSave"
        >
          {{ saving ? __('Saving…') : __('Save') }}
        </button>
        <span v-if="saved" class="text-xs text-green-600 dark:text-green-400">{{ __('Saved') }}</span>
        <span v-if="apiError" class="text-xs text-red-500">{{ apiError }}</span>
      </div>
    </div>

    <!-- ── Export ───────────────────────────────────────────────── -->
    <div v-else-if="activeTab === 4" class="max-w-2xl space-y-6">
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Export My Data') }}
        </h2>
        <p class="mb-4 text-xs text-gray-400 dark:text-gray-500">{{ __('Download your time entries as a CSV file.') }}</p>

        <div class="space-y-5">
          <!-- Preset selector -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">{{ __('Date range') }}</label>
            <select
              v-model="exportPreset"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            >
              <option v-for="p in EXPORT_PRESETS" :key="p.value" :value="p.value">{{ __(p.label) }}</option>
            </select>
          </div>

          <!-- Custom date pickers -->
          <div v-if="exportPreset === 'custom'" class="flex items-center gap-3">
            <input
              v-model="exportFromDate" type="date" :max="exportToDate || undefined"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
            <span class="text-gray-400 text-sm">→</span>
            <input
              v-model="exportToDate" type="date" :min="exportFromDate || undefined"
              class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800
                     px-3 py-2 text-sm text-gray-900 dark:text-white
                     focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>

          <button
            :disabled="exportPreset === 'custom' && (!exportFromDate || !exportToDate)"
            class="flex items-center gap-1.5 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium
                   text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            @click="downloadMyData"
          >
            <Download class="w-4 h-4" aria-hidden="true" />
            {{ __('Download CSV') }}
          </button>
        </div>
      </div>
    </div>
  </template>
</template>
