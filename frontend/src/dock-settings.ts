// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// ESM entry point for Watch's settings component.
// Dock's DockSettingsAppHost lazy-loads this bundle and renders WatchSettings
// inside the Dock SPA at /dock/settings/app/watch.
//
// This file is built as a separate Vite library entry: watch-settings.esm.js

export { default as WatchSettings } from './pages/Settings.vue'
