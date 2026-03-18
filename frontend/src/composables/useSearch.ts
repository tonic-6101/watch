// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

export interface SearchResult {
  label: string
  description: string
  route?: string
  icon: string
  meta: 'entry' | 'tag' | 'action' | 'nav'
  action?: string
  action_args?: Record<string, unknown>
}

export interface SearchSection {
  title: string
  results: SearchResult[]
}

const SECTION_MAP: Record<string, { endpoint: string; title: string }[]> = {
  '': [
    { endpoint: 'watch.api.search.navigation_shortcuts', title: 'Navigate' },
    { endpoint: 'watch.api.search.search_entries', title: 'Time Entries' },
    { endpoint: 'watch.api.search.search_tags', title: 'Tags' },
    { endpoint: 'watch.api.search.timer_action', title: 'Quick Action' },
  ],
  'time-entries': [
    { endpoint: 'watch.api.search.search_entries', title: 'Time Entries' },
  ],
  'tags': [
    { endpoint: 'watch.api.search.search_tags', title: 'Tags' },
  ],
}

export function useSearch() {
  const router = useRouter()
  const query = ref('')
  const scope = ref('')
  const sections = ref<SearchSection[]>([])
  const loading = ref(false)
  const open = ref(false)
  const activeIndex = ref(-1)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let abortController: AbortController | null = null

  const flatResults = (): SearchResult[] =>
    sections.value.flatMap(s => s.results)

  async function search() {
    const q = query.value.trim()
    if (!q) {
      sections.value = []
      open.value = false
      return
    }

    loading.value = true
    open.value = true
    activeIndex.value = -1

    // Cancel previous in-flight requests
    if (abortController) abortController.abort()
    abortController = new AbortController()
    const signal = abortController.signal

    const endpoints = SECTION_MAP[scope.value] ?? SECTION_MAP['']

    try {
      const responses = await Promise.all(
        endpoints.map(async ({ endpoint, title }) => {
          const res = await fetch(
            `/api/method/${endpoint}?query=${encodeURIComponent(q)}`,
            {
              headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' },
              signal,
            },
          )
          const data = await res.json()
          const results: SearchResult[] = data.message ?? []
          return { title, results }
        }),
      )

      if (signal.aborted) return

      sections.value = responses.filter(s => s.results.length > 0)
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        sections.value = []
      }
    } finally {
      if (!signal.aborted) loading.value = false
    }
  }

  function debouncedSearch() {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(search, 200)
  }

  watch(query, debouncedSearch)
  watch(scope, () => {
    if (query.value.trim()) search()
  })

  async function selectResult(result: SearchResult) {
    open.value = false
    query.value = ''

    if (result.action) {
      // Execute action (e.g. start timer)
      await fetch(`/api/method/${result.action}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '',
        },
        body: JSON.stringify(result.action_args ?? {}),
      })
      // Reload to reflect changes
      window.location.reload()
    } else if (result.route) {
      router.push(result.route)
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    const flat = flatResults()
    if (!open.value || !flat.length) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      activeIndex.value = Math.min(activeIndex.value + 1, flat.length - 1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      activeIndex.value = Math.max(activeIndex.value - 1, 0)
    } else if (e.key === 'Enter' && activeIndex.value >= 0) {
      e.preventDefault()
      selectResult(flat[activeIndex.value])
    } else if (e.key === 'Escape') {
      open.value = false
    }
  }

  function close() {
    open.value = false
  }

  return {
    query,
    scope,
    sections,
    loading,
    open,
    activeIndex,
    selectResult,
    handleKeydown,
    close,
    flatResults,
  }
}
