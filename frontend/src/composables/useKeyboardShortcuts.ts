// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { onMounted, onUnmounted } from 'vue'

export interface ShortcutHandlers {
  onTimerToggle:  () => void
  onTimerStop:    () => void
  onNewEntry:     () => void
  onGoToday:      () => void
  onGoWeek:       () => void
  onGoPrepare:    () => void
  onHelp:         () => void
  onEsc:          () => void
}

function isInputFocused(): boolean {
  const el = document.activeElement
  if (!el) return false
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)
    || (el as HTMLElement).getAttribute('contenteditable') === 'true'
}

function isModalOpen(): boolean {
  return !!(
    document.querySelector('.modal.show') ||
    document.querySelector('[data-dialog-open="true"]')
  )
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  function handle(e: KeyboardEvent) {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    if (isInputFocused() || isModalOpen()) return

    switch (e.key) {
      case 'T':
      case 't':
        e.preventDefault()
        handlers.onTimerToggle()
        break
      case 'S':
      case 's':
        e.preventDefault()
        handlers.onTimerStop()
        break
      case 'N':
      case 'n':
        e.preventDefault()
        handlers.onNewEntry()
        break
      case 'D':
      case 'd':
        e.preventDefault()
        handlers.onGoToday()
        break
      case 'W':
      case 'w':
        e.preventDefault()
        handlers.onGoWeek()
        break
      case 'B':
      case 'b':
        e.preventDefault()
        handlers.onGoPrepare()
        break
      case 'H':
      case 'h':
        e.preventDefault()
        handlers.onHelp()
        break
      case 'Escape':
        handlers.onEsc()
        break
    }
  }

  onMounted(()  => document.addEventListener('keydown', handle))
  onUnmounted(() => document.removeEventListener('keydown', handle))
}
