# Installation

## Requirements

| Component | Minimum Version |
|-----------|----------------|
| Frappe | 16.0+ |
| Python | 3.14+ |
| Node.js | 24+ |
| MariaDB | 10.6+ |
| Dock | 0.3.0+ |

Watch requires both `frappe` and `dock` as installed apps.

## Install

```bash
# Inside the Frappe Manager container
bench get-app https://github.com/tonic-6101/watch.git
bench --site your-site install-app watch
bench --site your-site migrate
```

## Configure Watch Settings

After installation, navigate to **Dock Settings > Watch** (or call the settings API directly). Watch Settings is a Single DocType with the following fields:

### General

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `default_entry_type` | Select | `billable` | Default type for new time entries (`billable`, `non-billable`, `internal`, `break`) |
| `lock_entries_older_than` | Int | `0` | Lock entries older than N days (0 = never lock) |
| `auto_stop_timer_after` | Int | `0` | Auto-stop running timers after N hours of inactivity (0 = never) |
| `idle_threshold_minutes` | Int | `15` | Minutes of inactivity before showing idle prompt |
| `daily_nudge_after` | Time | `None` | Time of day to nudge users who haven't logged time |

### Work Days

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `monday` | Check | `1` | Monday is a work day |
| `tuesday` | Check | `1` | Tuesday is a work day |
| `wednesday` | Check | `1` | Wednesday is a work day |
| `thursday` | Check | `1` | Thursday is a work day |
| `friday` | Check | `1` | Friday is a work day |
| `saturday` | Check | `0` | Saturday is a work day |
| `sunday` | Check | `0` | Sunday is a work day |

### Budget

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_budgets` | Check | `0` | Enable tag-level hour budgets |
| `budget_warning_threshold` | Percent | `80` | Notify when budget usage exceeds this percentage |
| `budget_period` | Select | `monthly` | Budget period (`weekly`, `monthly`, `quarterly`) |

### ERPNext Bridge

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `erpnext_sync_enabled` | Check | `0` | Enable ERPNext Timesheet sync |
| `erpnext_default_activity_type` | Data | `None` | Default Activity Type for synced timesheets |
| `erpnext_auto_sync` | Check | `0` | Automatically sync entries on creation |
| `erpnext_sync_direction` | Select | `watch_to_erpnext` | Sync direction |

### Integrations

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `slack_webhook_url` | Data | `None` | Slack webhook for daily summaries |
| `slack_channel` | Data | `None` | Target Slack channel |
| `linear_api_key` | Password | `None` | Linear API key for issue linking |
| `linear_team_id` | Data | `None` | Default Linear team |
| `github_token` | Password | `None` | GitHub personal access token |
| `github_default_repo` | Data | `None` | Default GitHub repository (owner/repo) |

## User Preferences

Each user can override defaults via **Watch User Settings** (or the preferences API):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `weekly_hour_target` | Float | `40.0` | Weekly hour target for progress tracking |
| `keyboard_shortcuts_enabled` | Check | `1` | Enable keyboard shortcuts |
| `pomodoro_work_minutes` | Int | `25` | Focus session work duration |
| `pomodoro_break_minutes` | Int | `5` | Focus session break duration |
| `pomodoro_sessions` | Int | `4` | Number of focus sessions before long break |
| `extension_token` | Data | `None` | Token for browser extension authentication |

## Update

```bash
cd apps/watch
git pull upstream develop
bench --site your-site migrate
bench build --app watch
```

## Uninstall

```bash
bench --site your-site uninstall-app watch
bench remove-app watch
```

Uninstalling Watch does not remove Watch data (entries, tags, settings) from the database. To fully remove data, drop the relevant tables manually after uninstalling.
