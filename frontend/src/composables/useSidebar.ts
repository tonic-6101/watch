// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { ref } from 'vue'

const STORAGE_KEY = 'watch-sidebar-collapsed'

const collapsed  = ref<boolean>(localStorage.getItem(STORAGE_KEY) === 'true')
const mobileOpen = ref<boolean>(false)

function isMobile(): boolean {
  return window.innerWidth <= 576
}

function toggle() {
  if (isMobile()) {
    mobileOpen.value = !mobileOpen.value
  } else {
    collapsed.value = !collapsed.value
    localStorage.setItem(STORAGE_KEY, String(collapsed.value))
  }
}

function closeMobile() {
  mobileOpen.value = false
}

export function useSidebar() {
  return { collapsed, mobileOpen, toggle, closeMobile, isMobile }
}
