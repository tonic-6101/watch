<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'
import { useUserSettings } from '@/composables/useUserSettings'

const emit = defineEmits<{ close: [] }>()

const {
  prefs, loaded, load: loadPrefs, save: savePrefs,
  generateExtensionToken, revokeExtensionToken,
} = useUserSettings()

// ── Preferences save state ──────────────────────────────────────────────────

const prefsSaving = ref(false)
const prefsSaved  = ref(false)
const prefsError  = ref<string | null>(null)

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

// ── Browser Extension token ─────────────────────────────────────────────────

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

// ── Load ────────────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!loaded.value) {
    try { await loadPrefs() } catch (e: any) {
      prefsError.value = e.message
    }
  }
})

function handleBackdropClick(e: MouseEvent) {
  if ((e.target as HTMLElement).dataset.backdrop !== undefined) {
    emit('close')
  }
}
</script>

<template>
  <!-- Backdrop -->
  <Transition
    enter-active-class="transition ease-out duration-200"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition ease-in duration-150"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      class="fixed inset-0 bg-black/30 z-40"
      data-backdrop
      @click="handleBackdropClick"
    >
      <!-- Panel -->
      <Transition
        enter-active-class="transition ease-out duration-200 transform"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transition ease-in duration-150 transform"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
        appear
      >
        <aside
          class="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-slate-950 shadow-xl z-50
                 flex flex-col overflow-hidden"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-700">
            <h2 class="text-base font-semibold text-gray-900 dark:text-slate-100">{{ __('My Preferences') }}</h2>
            <button
              class="w-8 h-8 flex items-center justify-center rounded-md
                     text-gray-500 dark:text-slate-500 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              :aria-label="__('Close')"
              @click="emit('close')"
            >
              <X class="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          <!-- Scrollable body -->
          <div class="flex-1 overflow-y-auto px-4 py-4 space-y-4">

            <!-- ── Preferences ─────────────────────────────────── -->
            <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
              <div class="px-4 py-3">
                <p class="text-xs text-gray-500 dark:text-slate-500">{{ __('Personal settings — only you can see these.') }}</p>
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

            <!-- ── Browser Extension ───────────────────────────── -->
            <div class="bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700">
              <div class="px-4 py-3">
                <h3 class="text-sm font-semibold text-gray-900 dark:text-slate-100">{{ __('Browser Extension') }}</h3>
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

          </div>
        </aside>
      </Transition>
    </div>
  </Transition>
</template>
