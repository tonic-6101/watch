// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { formatElapsed, formatDuration } from '../useTimer'

describe('formatElapsed', () => {
  it('formats zero seconds', () => {
    expect(formatElapsed(0)).toBe('00:00:00')
  })

  it('formats seconds only', () => {
    expect(formatElapsed(45)).toBe('00:00:45')
  })

  it('formats minutes and seconds', () => {
    expect(formatElapsed(125)).toBe('00:02:05')
  })

  it('formats hours, minutes, seconds', () => {
    expect(formatElapsed(3661)).toBe('01:01:01')
  })

  it('formats large values', () => {
    expect(formatElapsed(86400)).toBe('24:00:00')
  })

  it('handles negative values by clamping to 0', () => {
    expect(formatElapsed(-10)).toBe('00:00:00')
  })

  it('handles fractional seconds by flooring', () => {
    expect(formatElapsed(59.9)).toBe('00:00:59')
  })

  it('pads single digits with zeros', () => {
    expect(formatElapsed(1)).toBe('00:00:01')
    expect(formatElapsed(60)).toBe('00:01:00')
    expect(formatElapsed(3600)).toBe('01:00:00')
  })
})

describe('formatDuration', () => {
  it('formats seconds only when under 1 minute', () => {
    expect(formatDuration(45)).toBe('45s')
  })

  it('formats zero as 0s', () => {
    expect(formatDuration(0)).toBe('0s')
  })

  it('formats minutes only', () => {
    expect(formatDuration(300)).toBe('5m')
  })

  it('formats hours only', () => {
    expect(formatDuration(7200)).toBe('2h')
  })

  it('formats hours and minutes', () => {
    expect(formatDuration(5400)).toBe('1h 30m')
  })

  it('drops seconds in hours+minutes format', () => {
    expect(formatDuration(5431)).toBe('1h 30m')
  })

  it('handles negative values', () => {
    expect(formatDuration(-10)).toBe('0s')
  })
})

describe('useTimer composable', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    // Mock fetch for API calls
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ message: { state: 'stopped', elapsed_seconds: 0 } }),
    })
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('can import useTimer without errors', async () => {
    const { useTimer } = await import('../useTimer')
    expect(useTimer).toBeDefined()
    expect(typeof useTimer).toBe('function')
  })

  it('exports expected interface', async () => {
    const { useTimer } = await import('../useTimer')
    const timer = useTimer()
    expect(timer).toHaveProperty('state')
    expect(timer).toHaveProperty('elapsed')
    expect(timer).toHaveProperty('description')
    expect(timer).toHaveProperty('start')
    expect(timer).toHaveProperty('stop')
    expect(timer).toHaveProperty('pause')
    expect(timer).toHaveProperty('resume')
    expect(timer).toHaveProperty('loading')
    expect(timer).toHaveProperty('focusMode')
    expect(timer).toHaveProperty('focusPhase')
  })
})
