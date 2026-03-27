# Changelog

All notable changes to Watch will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Duration rounding (display-only): 7 increments (1m–60m), 3 directions (nearest/up/down) — raw data never mutated
- Custom date range report page (`/watch/range`) with presets (week, month, quarter, year, custom)
- Search API test coverage (`test_search_api.py`): entries, tags, timer action, navigation shortcuts

## [0.1.4] - 2026-03-26

### Added
- Pomodoro / focus mode with configurable work/break sessions
- Browser extension token generation and revocation API
- Slack, Linear, and GitHub integration endpoints (notify, search, comment)
- `watch_event_hooks` extensibility for third-party event listeners

## [0.1.3] - 2026-03-24

### Added
- Billing preparation view with hierarchical grouping (Contact → Project → Task)
- Forward bridge (`watch_billing_actions` hook) for invoicing apps
- CSV export for billable entries with mark-as-sent workflow
- ERPNext bridge: one-way sync to Timesheets (on_save, manual, scheduled modes)

## [0.1.2] - 2026-03-22

### Added
- Entry templates: favorites (1–9 keyboard slots) and day templates
- Bulk operations: multi-select with bulk tag add, entry type set, delete
- Entry duplication to same day or different date
- Tag management: merge, rename, archive, budget tracking

## [0.1.1] - 2026-03-20

### Added
- Weekly view with per-day breakdown, donut + bar charts, prev-week comparison
- Weekly hour target with progress bar and on-track hints
- Idle detection with retroactive stop prompt
- Keyboard shortcuts (T/S/N/D/W/B/H plus arrow navigation)
- Dark mode support (inherits from Dock)

## [0.1.0] - 2026-03-17

### Added
- Initial release: timer (start/stop/pause/resume), manual time entries
- Tag taxonomy with categories (Client, Project, Task, Other) and colors
- Daily view with quick-add bar and daily totals
- Entry types: billable, non-billable, internal
- Watch Settings (singleton) with work days, nudges, soft-lock
- Dock integration: timer API, app registry, global search (4 sections), settings hub, notifications
- Time Tracker role with auto-assignment
- German translation (233 strings)
- GDPR user data export and redaction support
