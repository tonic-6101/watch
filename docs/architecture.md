# Architecture

## Layer model

```
Layer 0   Frappe Core        (Contact, File, Event, User...)
Layer 1   Dock               coordination layer
Layer 2   Watch              time tracking domain app — you are here
Layer 3   Service Apps       (Drive, Repo, Jana)
```

Watch is a **Layer 2 domain app**. It owns all time tracking data and logic. Dock is a required dependency — Watch registers hooks that Dock reads at runtime to surface the timer widget, search results, and settings UI in the shared shell.

## DocTypes

Watch defines 9 DocTypes:

| DocType | Type | Purpose |
|---------|------|---------|
| Watch Entry | Document | Individual time entry (the core record) |
| Watch Timer | Single | Current timer state for the active user |
| Watch Tag | Document | Tags for categorizing time entries |
| Watch User Settings | Single | Per-user preferences (autoname = user) |
| Watch Settings | Single | Org-wide configuration |
| Watch Entry Tag | Child table | Many-to-many link between entries and tags |
| Watch Entry Template | Document | Saved entry templates for quick logging |
| Watch Entry Template Item | Child table | Template line items |
| Watch Entry Template Tag | Child table | Tags attached to template items |

## Permissions

Watch uses one custom role:

- **Time Tracker** — granted to all users who should log time. Allows creating, reading, and updating Watch Entries, Watch Tags, and Watch Entry Templates.
- **System Manager** — full access to Watch Settings and all records.

Row-level filtering is enforced via `if_owner` — users can only read and modify their own entries. System Managers can see all entries for reporting purposes.

## Timer state machine

The Watch Timer is a Single DocType that tracks the current timer state per user. It follows a strict state machine:

```
                  start
  [stopped] ─────────────> [running]
      ^                     │     ^
      │              pause  │     │  resume
      │                     v     │
      │                   [paused]
      │                     │
      └─────────────────────┘
              stop
```

**States:**

| State | Description |
|-------|-------------|
| `stopped` | No active timer. Entry fields are cleared. |
| `running` | Timer is counting. `started_at` records when the current run began. |
| `paused` | Timer is paused. `paused_at` records when the pause began. Elapsed time is preserved. |

**Transitions:**

| From | To | Action | Side effect |
|------|----|--------|-------------|
| stopped | running | `start_timer` | Creates pending Watch Entry, sets `started_at` |
| running | paused | `pause_timer` | Records `paused_at`, accumulates elapsed time |
| paused | running | `resume_timer` | Clears `paused_at`, updates `started_at` |
| running | stopped | `stop_timer` | Finalizes Watch Entry with calculated duration |
| paused | stopped | `stop_timer` | Finalizes Watch Entry with accumulated duration |

The `auto_stop_timer_after` setting triggers automatic stops for stale timers via a scheduled task.

## Pomodoro / Focus mode

Focus mode layers a Pomodoro-style session tracker on top of the timer state machine. When `start_focus` is called:

1. A normal timer starts (state = `running`).
2. The timer additionally tracks `focus_sessions_total`, `focus_sessions_completed`, `focus_work_minutes`, and `focus_break_minutes`.
3. When work time elapses, the timer transitions to a break period.
4. After all sessions complete, the timer stops and creates the final entry.

Focus mode reuses the same state machine — it is not a separate state. The `is_focus` flag on the timer distinguishes a focus session from a normal run.

## Soft dependencies

### Watch on Dock

Watch declares hooks that Dock reads at runtime. Watch never imports Dock code directly.

| Integration | Mechanism |
|-------------|-----------|
| Timer widget in top bar | `dock_timer_api` hook exposes 5 endpoints Dock calls |
| Global search results | `dock_search_sections` registers 4 search sections |
| Settings panel | `dock_settings_sections` registers ESM bundle with 5 subsections |
| Activity feed | `dock_activity_sources` registers Watch Entry |
| Budget notifications | `dock_notification_types` registers `budget_warning` and `budget_exceeded` |
| ERPNext bridge | `dock_bridges` registers timesheet sync |

### Watch on ERPNext

When ERPNext is installed and `erpnext_sync_enabled` is active, Watch can sync entries to ERPNext Timesheets. This is a soft dependency — Watch checks `"erpnext" in frappe.get_installed_apps()` before attempting any sync operations.

## Build outputs

Watch's Vite config produces two entry points:

| Entry | File | Purpose |
|-------|------|---------|
| SPA app | `watch-app.js` | Full Watch SPA at `/watch/*` |
| Settings ESM | `watch-settings.esm.js` | Lazy-loaded settings panel embedded in Dock Settings |

### Shared Vue runtime

Watch externalizes Vue and Vue Router to Dock's shared vendor builds:

```
/assets/dock/js/vendor/vue.esm.js
/assets/dock/js/vendor/vue-router.esm.js
```

This avoids duplicate Vue runtimes across the ecosystem.
