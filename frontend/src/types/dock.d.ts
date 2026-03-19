// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// Type declarations for Dock ESM bundle (dynamic URL import)
declare module '/assets/dock/js/dock-navbar.esm.js' {
  import type { DefineComponent } from 'vue'
  import type { RouteRecordRaw } from 'vue-router'

  export const DockNavbar: DefineComponent<{}, {}, any>
  export const DockLayout: DefineComponent<{}, {}, any>
  export const DockShareButton: DefineComponent<{}, {}, any>

  /** Shared page routes — spread into your router to render Dock pages in-app */
  export function dockSharedRoutes(prefix?: string): RouteRecordRaw[]
}
