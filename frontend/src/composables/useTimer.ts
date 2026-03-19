// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, computed, onMounted, onUnmounted } from 'vue'

// ── Types ───────────────────────────────────────────────────────────────

export type TimerState = 'stopped' | 'running' | 'paused'
export type EntryType = 'billable' | 'non-billable' | 'internal'

export interface TimerData {
  state: TimerState
  elapsed_seconds: number
  accumulated_seconds: number
  description: string
  tags: string[]
  entry_type: EntryType
  active_entry: string | null
  active_entry_date: string | null
  started_at: string | null
  // Focus mode
  focus_mode: boolean
  focus_phase: 'work' | 'break'
  focus_session_number: number
  focus_total_sessions: number
  focus_work_minutes: number
  focus_break_minutes: number
  focus_description: string | null
}

export type FocusPhase = 'work' | 'break'

// ── API helper ──────────────────────────────────────────────────────────

async function call<T = any>(
  method: string,
  params: Record<string, unknown> = {},
  httpMethod: 'GET' | 'POST' = 'POST',
): Promise<T> {
  let url = `/api/method/${method}`
  if (httpMethod === 'GET' && Object.keys(params).length) {
    const qs = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => [k, String(v)]),
    )
    url += `?${qs.toString()}`
  }
  const res = await fetch(url, {
    method: httpMethod,
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
    },
    body: httpMethod !== 'GET' ? JSON.stringify(params) : undefined,
  })
  const data = await res.json()
  if (!res.ok || data.exc) {
    let msg = 'Request failed'
    try {
      msg = JSON.parse(data._server_messages ?? '[]')[0]?.message ?? data.exc ?? msg
    } catch { /* ignore */ }
    throw new Error(msg)
  }
  return data.message as T
}

// ── Elapsed display helpers ─────────────────────────────────────────────

export function formatElapsed(seconds: number): string {
  const t = Math.max(0, Math.floor(seconds))
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  const s = t % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function formatDuration(seconds: number): string {
  const t = Math.max(0, Math.floor(seconds))
  const h = Math.floor(t / 3600)
  const m = Math.floor((t % 3600) / 60)
  if (h > 0 && m > 0) return `${h}h ${m}m`
  if (h > 0) return `${h}h`
  if (m > 0) return `${m}m`
  return `${t}s`
}

// ── Singleton timer state ───────────────────────────────────────────────
// Shared across all component instances so the widget and any other
// consumer always see the same live elapsed.

const state            = ref<TimerState>('stopped')
const elapsed          = ref(0)            // live ticking seconds
const accumulatedSeconds = ref(0)
const description      = ref('')
const tags             = ref<string[]>([])
const entryType      = ref<EntryType>('billable')
const activeEntry      = ref<string | null>(null)
const activeEntryDate  = ref<string | null>(null)
const startedAt        = ref<string | null>(null)
const loading          = ref(false)
const error            = ref<string | null>(null)

// Focus mode state
const focusMode          = ref(false)
const focusPhase         = ref<FocusPhase>('work')
const focusSessionNumber = ref(1)
const focusTotalSessions = ref(4)
const focusWorkMinutes   = ref(25)
const focusBreakMinutes  = ref(5)
const focusDescription   = ref<string | null>(null)

let tickInterval: ReturnType<typeof setInterval> | null = null
let pollInterval:  ReturnType<typeof setInterval> | null = null
let initialized = false
let mountCount = 0

function startTicking() {
  stopTicking()
  tickInterval = setInterval(() => {
    if (state.value === 'running') elapsed.value += 1
  }, 1000)
}

function stopTicking() {
  if (tickInterval) { clearInterval(tickInterval); tickInterval = null }
}

async function fetchEntryTags(entryName: string): Promise<string[]> {
  try {
    const res = await call<any>('frappe.client.get', {
      doctype: 'Watch Entry',
      name: entryName,
    })
    return (res?.tags ?? []).map((t: any) => t.tag_name ?? t.tag)
  } catch {
    return []
  }
}

async function fetchEntryType(entryName: string): Promise<EntryType> {
  try {
    const res = await call<any>('frappe.client.get_value', {
      doctype: 'Watch Entry',
      filters: { name: entryName },
      fieldname: 'entry_type',
    })
    return (res?.entry_type ?? 'billable') as EntryType
  } catch {
    return 'billable'
  }
}

export function useTimer() {
  // ── Load / sync state from server ──────────────────────────────────

  async function load() {
    try {
      const data = await call<TimerData>(
        'watch.api.timer.get_timer_state',
        {},
        'GET',
      )
      const prevState = state.value
      state.value              = data.state
      accumulatedSeconds.value = data.accumulated_seconds
      description.value        = data.description ?? ''
      activeEntry.value        = data.active_entry
      activeEntryDate.value    = data.active_entry_date ?? null
      startedAt.value          = data.started_at
      focusMode.value          = data.focus_mode ?? false
      focusPhase.value         = data.focus_phase ?? 'work'
      focusSessionNumber.value = data.focus_session_number ?? 1
      focusTotalSessions.value = data.focus_total_sessions ?? 4
      focusWorkMinutes.value   = data.focus_work_minutes ?? 25
      focusBreakMinutes.value  = data.focus_break_minutes ?? 5
      focusDescription.value   = data.focus_description ?? null

      if (data.state !== 'stopped') {
        // Only hard-set elapsed on first load or state change.
        // During normal polling while already ticking, only correct
        // if server and client have drifted by more than 2 seconds.
        const alreadyTicking = prevState === data.state && tickInterval !== null
        if (alreadyTicking) {
          const drift = Math.abs(elapsed.value - data.elapsed_seconds)
          if (drift > 2) elapsed.value = data.elapsed_seconds
        } else {
          elapsed.value = data.elapsed_seconds
        }
        // Fetch tags + entry type from the active entry
        if (data.active_entry) {
          const [entryTags, fetchedEntryType] = await Promise.all([
            fetchEntryTags(data.active_entry),
            fetchEntryType(data.active_entry),
          ])
          tags.value        = entryTags
          entryType.value = fetchedEntryType
        }
      } else {
        elapsed.value = 0
        tags.value    = []
        entryType.value = 'billable'
      }

      if (data.state === 'running') startTicking()
      else stopTicking()
    } catch (e: any) {
      error.value = e.message
    }
  }

  // ── Actions ────────────────────────────────────────────────────────

  async function start(
    desc: string,
    tagList: string[],
    bt: EntryType,
  ): Promise<void> {
    loading.value = true
    error.value   = null
    try {
      const res = await call('watch.api.timer.start_timer', {
        description: desc || null,
        tags: JSON.stringify(tagList),
        entry_type: bt,
      })
      state.value              = 'running'
      elapsed.value            = 0
      accumulatedSeconds.value = 0
      description.value        = desc
      tags.value               = tagList
      entryType.value        = bt
      activeEntry.value        = res.entry
      activeEntryDate.value    = new Date().toISOString().slice(0, 10)
      startTicking()
    } finally {
      loading.value = false
    }
  }

  async function pause(): Promise<void> {
    loading.value = true
    try {
      const res = await call('watch.api.timer.pause_timer')
      state.value              = 'paused'
      accumulatedSeconds.value = res.accumulated_seconds
      elapsed.value            = res.accumulated_seconds
      stopTicking()
    } finally {
      loading.value = false
    }
  }

  async function resume(): Promise<void> {
    loading.value = true
    try {
      await call('watch.api.timer.resume_timer')
      state.value = 'running'
      startTicking()
    } finally {
      loading.value = false
    }
  }

  async function stop(notes: string): Promise<{ entry: any }> {
    loading.value = true
    try {
      const res = await call('watch.api.timer.stop_timer', { notes: notes || null })
      const savedElapsed = elapsed.value
      state.value              = 'stopped'
      elapsed.value            = 0
      accumulatedSeconds.value = 0
      description.value        = ''
      tags.value               = []
      entryType.value        = 'billable'
      activeEntry.value        = null
      activeEntryDate.value    = null
      startedAt.value          = null
      stopTicking()
      return { entry: { ...res.entry, _saved_elapsed: savedElapsed } }
    } finally {
      loading.value = false
    }
  }

  async function update(
    desc: string,
    tagList: string[],
    bt: EntryType,
  ): Promise<void> {
    loading.value = true
    try {
      await call('watch.api.timer.update_timer', {
        description: desc,
        tags: JSON.stringify(tagList),
        entry_type: bt,
      })
      description.value = desc
      tags.value        = tagList
      entryType.value = bt
    } finally {
      loading.value = false
    }
  }

  // ── Focus actions ────────────────────────────────────────────────────

  async function startFocus(
    desc: string,
    tagList: string[],
    bt: EntryType,
    sessions: number,
    workMins: number,
    breakMins: number,
  ): Promise<void> {
    loading.value = true
    error.value   = null
    try {
      const res = await call('watch.api.timer.start_focus', {
        description: desc || null,
        tags: JSON.stringify(tagList),
        entry_type: bt,
        sessions,
        work_minutes: workMins,
        break_minutes: breakMins,
      })
      state.value              = 'running'
      elapsed.value            = 0
      accumulatedSeconds.value = 0
      description.value        = desc
      tags.value               = tagList
      entryType.value          = bt
      activeEntry.value        = res.entry
      activeEntryDate.value    = new Date().toISOString().slice(0, 10)
      focusMode.value          = true
      focusPhase.value         = 'work'
      focusSessionNumber.value = 1
      focusTotalSessions.value = sessions
      focusWorkMinutes.value   = workMins
      focusBreakMinutes.value  = breakMins
      focusDescription.value   = desc || null
      startTicking()
    } finally {
      loading.value = false
    }
  }

  async function endFocusSession(): Promise<{ completed: boolean; focus_phase?: string; focus_break_minutes?: number }> {
    loading.value = true
    try {
      const res = await call('watch.api.timer.end_focus_session')
      if (res.completed) {
        state.value              = 'stopped'
        elapsed.value            = 0
        accumulatedSeconds.value = 0
        focusMode.value          = false
        activeEntry.value        = null
        stopTicking()
      } else {
        state.value    = 'stopped'
        elapsed.value  = 0
        focusPhase.value = 'break'
        activeEntry.value = null
        stopTicking()
      }
      return res
    } finally {
      loading.value = false
    }
  }

  async function skipBreak(): Promise<{ focus_session_number: number; entry: string }> {
    loading.value = true
    try {
      const res = await call('watch.api.timer.skip_break', {
        entry_type: entryType.value,
        tags: JSON.stringify(tags.value),
      })
      focusSessionNumber.value = res.focus_session_number
      focusPhase.value         = 'work'
      state.value              = 'running'
      elapsed.value            = 0
      activeEntry.value        = res.entry
      startTicking()
      return res
    } finally {
      loading.value = false
    }
  }

  async function endFocus(): Promise<void> {
    loading.value = true
    try {
      await call('watch.api.timer.end_focus')
      state.value              = 'stopped'
      elapsed.value            = 0
      accumulatedSeconds.value = 0
      description.value        = ''
      tags.value               = []
      activeEntry.value        = null
      activeEntryDate.value    = null
      focusMode.value          = false
      focusPhase.value         = 'work'
      focusSessionNumber.value = 1
      focusDescription.value   = null
      stopTicking()
    } finally {
      loading.value = false
    }
  }

  // ── Realtime ────────────────────────────────────────────────────────
  // Frappe publishes dock_timer_update via window.frappe.realtime when available.

  function listenRealtime() {
    const rt = (window as any).frappe?.realtime
    if (!rt) return
    rt.on('dock_timer_update', (payload: any) => {
      if (payload.state) state.value = payload.state
      if (payload.accumulated_seconds !== undefined)
        accumulatedSeconds.value = payload.accumulated_seconds
      if (payload.description !== undefined) description.value = payload.description
      if (payload.focus_mode !== undefined) focusMode.value = payload.focus_mode
      if (payload.focus_phase !== undefined) focusPhase.value = payload.focus_phase
      if (payload.focus_session_number !== undefined) focusSessionNumber.value = payload.focus_session_number
      if (payload.focus_total_sessions !== undefined) focusTotalSessions.value = payload.focus_total_sessions
      if (payload.focus_break_minutes !== undefined) focusBreakMinutes.value = payload.focus_break_minutes
      if (payload.state === 'running') startTicking()
      if (payload.state === 'stopped' || payload.state === 'paused') stopTicking()
    })
  }

  // ── Lifecycle ───────────────────────────────────────────────────────

  onMounted(async () => {
    mountCount++
    if (!initialized) {
      initialized = true
      await load()
      listenRealtime()
      pollInterval = setInterval(load, 30_000)
    }
  })

  onUnmounted(() => {
    mountCount--
    // Only tear down when no component instances remain
    if (mountCount <= 0) {
      mountCount = 0
      stopTicking()
      if (pollInterval) { clearInterval(pollInterval); pollInterval = null }
      initialized = false
    }
  })

  return {
    // state
    state,
    elapsed,
    description,
    tags,
    entryType,
    activeEntry,
    activeEntryDate,
    loading,
    error,
    // focus state
    focusMode,
    focusPhase,
    focusSessionNumber,
    focusTotalSessions,
    focusWorkMinutes,
    focusBreakMinutes,
    focusDescription,
    // derived
    isRunning:  computed(() => state.value === 'running'),
    isPaused:   computed(() => state.value === 'paused'),
    isStopped:  computed(() => state.value === 'stopped'),
    isActive:   computed(() => state.value !== 'stopped'),
    // actions
    load,
    start,
    pause,
    resume,
    stop,
    update,
    // focus actions
    startFocus,
    endFocusSession,
    skipBreak,
    endFocus,
  }
}
