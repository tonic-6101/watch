// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useToast } from '../useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Clear toasts between tests
    const { toasts } = useToast()
    toasts.value = []
  })

  it('shows a toast and returns an id', () => {
    const { show, toasts } = useToast()
    const id = show('Hello')
    expect(typeof id).toBe('number')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Hello')
  })

  it('auto-dismisses after duration', () => {
    const { show, toasts } = useToast()
    show('Temporary', { duration: 2000 })
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(2000)
    expect(toasts.value).toHaveLength(0)
  })

  it('uses default duration of 4000ms', () => {
    const { show, toasts } = useToast()
    show('Default')
    expect(toasts.value[0].duration).toBe(4000)
    vi.advanceTimersByTime(3999)
    expect(toasts.value).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(toasts.value).toHaveLength(0)
  })

  it('manually dismisses a toast', () => {
    const { show, dismiss, toasts } = useToast()
    const id = show('Dismissable')
    expect(toasts.value).toHaveLength(1)
    dismiss(id)
    expect(toasts.value).toHaveLength(0)
  })

  it('supports action on toast', () => {
    const handler = vi.fn()
    const { show, toasts } = useToast()
    show('With action', { action: { label: 'Undo', handler } })
    expect(toasts.value[0].action?.label).toBe('Undo')
    toasts.value[0].action?.handler()
    expect(handler).toHaveBeenCalledOnce()
  })

  it('handles multiple toasts', () => {
    const { show, toasts } = useToast()
    show('First')
    show('Second')
    show('Third')
    expect(toasts.value).toHaveLength(3)
    expect(toasts.value.map((t) => t.message)).toEqual(['First', 'Second', 'Third'])
  })

  it('assigns unique ids', () => {
    const { show, toasts } = useToast()
    show('A')
    show('B')
    const ids = toasts.value.map((t) => t.id)
    expect(new Set(ids).size).toBe(2)
  })
})
