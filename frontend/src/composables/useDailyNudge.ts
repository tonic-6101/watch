// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, type Ref } from 'vue'
import { useTimer } from './useTimer'

const LS_PREFIX = 'watch_daily_nudge_dismissed_'

/**
 * Daily work nudge — shown when:
 * 1. Today is a configured work day
 * 2. Current time >= daily_nudge_after (default 10:00)
 * 3. Current user has zero entries for today
 * 4. No timer is currently running
 * 5. User has not dismissed it today
 */
export function useDailyNudge(activeDate: Ref<string>) {
  const visible = ref(false)
  const timer = useTimer()

  function todayStr(): string {
    return new Date().toISOString().slice(0, 10)
  }

  function isDismissedToday(): boolean {
    return !!localStorage.getItem(LS_PREFIX + todayStr())
  }

  async function check() {
    visible.value = false

    // Only on today's view
    if (activeDate.value !== todayStr()) return

    // Already dismissed
    if (isDismissedToday()) return

    // Timer running means user is already tracking
    if (timer.state.value === 'running' || timer.state.value === 'paused') return

    try {
      // Fetch settings for daily_nudge_after and work days
      const [settingsRes, summaryRes] = await Promise.all([
        fetch('/api/method/watch.api.settings.get_settings', {
          headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
        }),
        fetch(
          `/api/method/watch.api.time_entry.get_daily_summary?date=${todayStr()}`,
          { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
        ),
      ])

      const settings = (await settingsRes.json()).message ?? {}
      const summary = (await summaryRes.json()).message ?? {}

      // Check if daily nudge is enabled
      const nudgeAfter = settings.daily_nudge_after
      if (!nudgeAfter) return

      // Check if today is a work day
      const dayIndex = new Date().getDay()
      // JS getDay: 0=Sun, we need 0=Mon convention
      const weekdayMap: Record<number, string> = {
        1: 'work_mon', 2: 'work_tue', 3: 'work_wed',
        4: 'work_thu', 5: 'work_fri', 6: 'work_sat', 0: 'work_sun',
      }
      const dayField = weekdayMap[dayIndex]
      if (!settings[dayField]) return

      // Check if current time >= nudge_after
      const now = new Date()
      const [h, m] = String(nudgeAfter).split(':').map(Number)
      const nudgeTime = new Date()
      nudgeTime.setHours(h, m, 0, 0)
      if (now < nudgeTime) return

      // Check if user has zero entries today
      const entries = summary.entries ?? []
      if (entries.length > 0) return

      visible.value = true
    } catch {
      /* silently ignore nudge errors */
    }
  }

  function dismiss() {
    localStorage.setItem(LS_PREFIX + todayStr(), '1')
    visible.value = false
  }

  return {
    visible,
    check,
    dismiss,
  }
}
