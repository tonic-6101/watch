// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref } from 'vue'
import type { EntryType } from './useTimer'

// ── Types ───────────────────────────────────────────────────────────────

export interface TagMeta {
  name: string
  tag_name: string
  color: string | null
  category: string | null
}

export interface TimeEntry {
  name: string
  date: string
  start_time: string | null
  end_time: string | null
  duration_hours: number
  description: string | null
  entry_type: EntryType
  entry_status: 'draft' | 'sent'
  is_running: number
  tag_names: string[]
  tag_meta: TagMeta[]
  linear_issue: string | null
  github_ref: string | null
}

export interface CreateParams {
  date: string
  duration_hours?: number | null
  start_time?: string | null
  end_time?: string | null
  description?: string | null
  entry_type?: EntryType
  tags?: string[]
  linear_issue?: string | null
  github_ref?: string | null
}

export interface UpdateParams {
  date?: string
  duration_hours?: number | null
  start_time?: string | null
  end_time?: string | null
  description?: string | null
  entry_type?: EntryType
  tags?: string[]
  linear_issue?: string | null
  github_ref?: string | null
}

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

// ── Helpers ─────────────────────────────────────────────────────────────

export function formatHours(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  if (h > 0 && m > 0) return `${h}h ${m}m`
  if (h > 0) return `${h}h`
  if (m > 0) return `${m}m`
  return '0m'
}

/** Parse "h:mm" → decimal hours, or null if invalid. */
export function parseDurationInput(val: string): number | null {
  const match = val.match(/^(\d+):(\d{2})$/)
  if (!match) return null
  const h = parseInt(match[1])
  const m = parseInt(match[2])
  if (m >= 60) return null
  return h + m / 60
}

/** Decimal hours → "h:mm" */
export function formatDurationInput(hours: number): string {
  const h = Math.floor(hours)
  const m = Math.round((hours - h) * 60)
  return `${h}:${String(m).padStart(2, '0')}`
}

/** "HH:MM" or "HH:MM:SS" → minutes from midnight, or null */
export function timeToMinutes(t: string): number | null {
  const match = t.match(/^(\d{2}):(\d{2})/)
  if (!match) return null
  return parseInt(match[1]) * 60 + parseInt(match[2])
}

/** Minutes from midnight → "HH:MM" */
export function minutesToTime(m: number): string {
  const h = Math.floor(m / 60) % 24
  const min = m % 60
  return `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}`
}

/** Number of days between today and a date string (positive = past). */
export function daysAgo(dateStr: string): number {
  const d = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  d.setHours(0, 0, 0, 0)
  return Math.round((today.getTime() - d.getTime()) / 86_400_000)
}

// ── Composable ──────────────────────────────────────────────────────────

export function useEntries() {
  const entries       = ref<TimeEntry[]>([])
  const totalHours    = ref(0)
  const billableHours = ref(0)
  const loading       = ref(false)
  const error         = ref<string | null>(null)

  async function load(date: string) {
    if (!date) return
    loading.value = true
    error.value   = null
    try {
      const res = await call<any>('watch.api.time_entry.get_daily_summary', { date }, 'GET')
      entries.value       = res.entries ?? []
      totalHours.value    = res.total_hours ?? 0
      billableHours.value = res.billable_hours ?? 0
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function create(params: CreateParams): Promise<TimeEntry> {
    const res = await call<TimeEntry>('watch.api.time_entry.create_entry', {
      ...params,
      tags: params.tags ? JSON.stringify(params.tags) : undefined,
    })
    entries.value = [res, ...entries.value]
    totalHours.value    = +(totalHours.value + (res.duration_hours ?? 0)).toFixed(4)
    billableHours.value = res.entry_type === 'billable'
      ? +(billableHours.value + (res.duration_hours ?? 0)).toFixed(4)
      : billableHours.value
    return res
  }

  async function update(name: string, params: UpdateParams): Promise<TimeEntry> {
    const res = await call<TimeEntry>('watch.api.time_entry.update_entry', {
      entry_name: name,
      ...params,
      tags: params.tags !== undefined ? JSON.stringify(params.tags) : undefined,
    })
    const idx = entries.value.findIndex(e => e.name === name)
    if (idx !== -1) entries.value[idx] = res
    // Recompute totals from current entries
    const billable = entries.value.filter(e => e.entry_type === 'billable')
    totalHours.value    = +entries.value.reduce((s, e) => s + (e.duration_hours ?? 0), 0).toFixed(4)
    billableHours.value = +billable.reduce((s, e) => s + (e.duration_hours ?? 0), 0).toFixed(4)
    return res
  }

  async function remove(name: string): Promise<void> {
    await call('watch.api.time_entry.delete_entry', { entry_name: name })
    const removed = entries.value.find(e => e.name === name)
    entries.value = entries.value.filter(e => e.name !== name)
    if (removed) {
      totalHours.value    = +(totalHours.value - (removed.duration_hours ?? 0)).toFixed(4)
      billableHours.value = removed.entry_type === 'billable'
        ? +(billableHours.value - (removed.duration_hours ?? 0)).toFixed(4)
        : billableHours.value
    }
  }

  return {
    entries,
    totalHours,
    billableHours,
    loading,
    error,
    load,
    create,
    update,
    remove,
  }
}
