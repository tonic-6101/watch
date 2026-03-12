// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref } from 'vue'

export interface UserPreferences {
  weekly_hour_target: number
  enable_keyboard_shortcuts: 0 | 1
  focus_work_minutes: number
  focus_break_minutes: number
  focus_sessions: number
  extension_token_active: 0 | 1
}

const prefs = ref<UserPreferences>({
  weekly_hour_target: 0,
  enable_keyboard_shortcuts: 1,
  focus_work_minutes: 25,
  focus_break_minutes: 5,
  focus_sessions: 4,
  extension_token_active: 0,
})

const loaded = ref(false)
const loading = ref(false)

async function load(): Promise<UserPreferences> {
  loading.value = true
  try {
    const res = await fetch('/api/method/watch.api.user_settings.get_preferences', {
      headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Load failed')
    Object.assign(prefs.value, data.message)
    loaded.value = true
    return prefs.value
  } finally {
    loading.value = false
  }
}

async function save(updates: Partial<UserPreferences>): Promise<UserPreferences> {
  loading.value = true
  try {
    const res = await fetch('/api/method/watch.api.user_settings.save_preferences', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
      },
      body: JSON.stringify(updates),
    })
    const data = await res.json()
    if (!res.ok || data.exc) throw new Error(data.exc ?? 'Save failed')
    Object.assign(prefs.value, data.message)
    return prefs.value
  } finally {
    loading.value = false
  }
}

async function generateExtensionToken(): Promise<string> {
  const res = await fetch('/api/method/watch.api.user_settings.generate_extension_token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
  })
  const data = await res.json()
  if (!res.ok || data.exc) throw new Error(data.exc ?? 'Token generation failed')
  prefs.value.extension_token_active = 1
  return data.message.token as string
}

async function revokeExtensionToken(): Promise<void> {
  const res = await fetch('/api/method/watch.api.user_settings.revoke_extension_token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
  })
  const data = await res.json()
  if (!res.ok || data.exc) throw new Error(data.exc ?? 'Token revocation failed')
  prefs.value.extension_token_active = 0
}

export function useUserSettings() {
  return { prefs, loaded, loading, load, save, generateExtensionToken, revokeExtensionToken }
}
