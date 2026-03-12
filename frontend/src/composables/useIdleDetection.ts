// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, onMounted, onUnmounted } from 'vue'
import { useTimer } from './useTimer'

export interface IdlePromptData {
  hiddenAt: Date
  awayMinutes: number
}

const LS_KEY = 'watch_hidden_at'

/**
 * Tracks tab visibility via the Page Visibility API.
 * When the user returns with a running timer after being away
 * longer than idle_threshold_minutes, exposes prompt data.
 */
export function useIdleDetection() {
  const timer = useTimer()
  const prompt = ref<IdlePromptData | null>(null)
  const dismissed = ref(false)

  let thresholdMinutes = 10

  async function fetchThreshold() {
    try {
      const res = await fetch(
        '/api/method/watch.api.settings.get_settings',
        { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
      )
      const data = await res.json()
      const val = data.message?.idle_threshold_minutes
      if (val !== undefined && val !== null) thresholdMinutes = Number(val)
    } catch { /* use default */ }
  }

  function onVisibilityChange() {
    if (document.hidden) {
      localStorage.setItem(LS_KEY, Date.now().toString())
    } else {
      const hiddenAt = localStorage.getItem(LS_KEY)
      localStorage.removeItem(LS_KEY)

      if (!hiddenAt || dismissed.value) return
      if (thresholdMinutes <= 0) return
      if (timer.state.value !== 'running' && timer.state.value !== 'paused') return

      const awayMs = Date.now() - Number(hiddenAt)
      const awayMinutes = awayMs / 60_000

      if (awayMinutes >= thresholdMinutes) {
        prompt.value = {
          hiddenAt: new Date(Number(hiddenAt)),
          awayMinutes,
        }
      }
    }
  }

  function dismiss() {
    prompt.value = null
    dismissed.value = true
  }

  /** Keep all — close banner, timer continues untouched. */
  function keepAll() {
    prompt.value = null
  }

  /** Stop at hidden_at — retroactive stop via API. */
  async function stopAt() {
    if (!prompt.value) return
    const stopAtIso = prompt.value.hiddenAt.toISOString()
    try {
      await fetch('/api/method/watch.api.timer.stop_timer_at', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
        },
        body: JSON.stringify({ stop_at: stopAtIso }),
      })
      await timer.load()
    } finally {
      prompt.value = null
    }
  }

  /** Stop now — standard stop flow. */
  async function stopNow() {
    try {
      await timer.stop('')
    } finally {
      prompt.value = null
    }
  }

  onMounted(async () => {
    await fetchThreshold()
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    prompt,
    dismiss,
    keepAll,
    stopAt,
    stopNow,
  }
}
