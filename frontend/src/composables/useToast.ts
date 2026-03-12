// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref } from 'vue'

export interface ToastAction {
  label: string
  handler: () => void
}

export interface Toast {
  id: number
  message: string
  action?: ToastAction
  duration: number
}

let nextId = 0
const toasts = ref<Toast[]>([])

function show(message: string, opts?: { action?: ToastAction; duration?: number }) {
  const id = nextId++
  const duration = opts?.duration ?? 4000
  const toast: Toast = { id, message, action: opts?.action, duration }
  toasts.value.push(toast)
  setTimeout(() => dismiss(id), duration)
  return id
}

function dismiss(id: number) {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

export function useToast() {
  return { toasts, show, dismiss }
}
