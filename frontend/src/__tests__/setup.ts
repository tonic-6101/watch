// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { vi } from 'vitest'

// Mock frappe global (used by some composables indirectly)
vi.stubGlobal('frappe', {
  call: vi.fn(),
  xcall: vi.fn(),
  session: { user: 'test@example.com' },
})

// Mock window.csrf_token (used by useTimer's call() helper)
vi.stubGlobal('csrf_token', 'test-csrf-token')

// Mock fetch globally for API calls
vi.stubGlobal('fetch', vi.fn())
