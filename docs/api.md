# API Reference

All endpoints use the Frappe RPC convention:

```
POST /api/method/watch.api.<module>.<function>
Content-Type: application/json
```

Authenticated via Frappe session cookie or token.

---

## Timer

### `start_timer`

```
watch.api.timer.start_timer
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context_label` | string | `None` | What you're working on |
| `description` | string | `None` | Optional notes |
| `tags` | string | `None` | Comma-separated tag names |
| `entry_type` | string | `None` | `billable`, `non-billable`, `internal`, `break` |
| `contact` | string | `None` | Linked Contact name |
| `context_type` | string | `None` | Linked DocType |
| `context_name` | string | `None` | Linked document name |

**Returns:** `{state, started_at, context_label, entry_name, entry_type, tags}`

### `stop_timer`

```
watch.api.timer.stop_timer
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `notes` | string | `None` | Final notes appended to the entry |

**Returns:** `{state, entry_name, duration, context_label}`

### `pause_timer`

```
watch.api.timer.pause_timer
```

**Returns:** `{state, paused_at, elapsed_seconds}`

### `resume_timer`

```
watch.api.timer.resume_timer
```

**Returns:** `{state, started_at, elapsed_seconds}`

### `get_timer_state`

```
watch.api.timer.get_timer_state
```

**Returns:** `{state, elapsed_seconds, started_at, paused_at, context_label, entry_name, entry_type, tags, contact, contact_name, context_type, context_name, context_display, is_focus, focus_sessions_total, focus_sessions_completed, focus_work_minutes, focus_break_minutes}`

### `stop_timer_at`

```
watch.api.timer.stop_timer_at
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `stop_time` | string | ISO datetime to use as the stop time |

Stops the timer and sets the entry's end time to the given value. Useful for correcting entries after idle periods.

**Returns:** `{state, entry_name, duration}`

### `update_timer`

```
watch.api.timer.update_timer
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context_label` | string | `None` | |
| `description` | string | `None` | |
| `tags` | string | `None` | Comma-separated |
| `entry_type` | string | `None` | |
| `contact` | string | `None` | |
| `context_type` | string | `None` | |
| `context_name` | string | `None` | |

Updates the context of a running or paused timer without stopping it.

**Returns:** updated timer state

### `start_focus`

```
watch.api.timer.start_focus
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context_label` | string | `None` | |
| `description` | string | `None` | |
| `tags` | string | `None` | |
| `entry_type` | string | `"billable"` | |
| `sessions` | int | `4` | Number of work sessions |
| `work_minutes` | int | `25` | Work duration per session |
| `break_minutes` | int | `5` | Break duration per session |
| `contact` | string | `None` | |
| `context_type` | string | `None` | |
| `context_name` | string | `None` | |

**Returns:** `{state, is_focus, focus_sessions_total, focus_work_minutes, focus_break_minutes, started_at}`

### `end_focus_session`

```
watch.api.timer.end_focus_session
```

Completes the current focus work period and transitions to break.

**Returns:** `{state, focus_sessions_completed, on_break}`

### `skip_break`

```
watch.api.timer.skip_break
```

Skips the current break period and starts the next work session immediately.

**Returns:** `{state, focus_sessions_completed, started_at}`

### `end_focus`

```
watch.api.timer.end_focus
```

Ends the entire focus session early, stopping the timer and finalizing the entry.

**Returns:** `{state, entry_name, duration, focus_sessions_completed}`

### `get_context_options`

```
watch.api.timer.get_context_options
```

**Returns:** `[{doctype, label, icon}, ...]` — available context types for the timer picker.

---

## Time Entry

### `create_entry`

```
watch.api.time_entry.create_entry
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `date` | string | today | ISO date |
| `start_time` | string | *(required)* | ISO datetime |
| `end_time` | string | *(required)* | ISO datetime |
| `context_label` | string | `None` | |
| `description` | string | `None` | |
| `entry_type` | string | `None` | Falls back to `default_entry_type` |
| `tags` | list | `None` | Tag names |
| `contact` | string | `None` | |
| `context_type` | string | `None` | |
| `context_name` | string | `None` | |

**Returns:** full Watch Entry dict

### `update_entry`

```
watch.api.time_entry.update_entry
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry_name` | string | Watch Entry name |
| `**fields` | any | Any editable field |

Locked entries (older than `lock_entries_older_than`) cannot be updated.

**Returns:** updated Watch Entry dict

### `delete_entry`

```
watch.api.time_entry.delete_entry
```

| Parameter | Type |
|-----------|------|
| `entry_name` | string |

**Returns:** `{deleted: entry_name}`

### `get_daily_summary`

```
watch.api.time_entry.get_daily_summary
```

| Parameter | Type | Default |
|-----------|------|---------|
| `date` | string | today |
| `user` | string | current user |

**Returns:** `{entries: [...], total_hours, total_seconds, by_type: {billable, non_billable, internal, break}}`

### `get_weekly_summary`

```
watch.api.time_entry.get_weekly_summary
```

| Parameter | Type | Default |
|-----------|------|---------|
| `date` | string | today |
| `user` | string | current user |

**Returns:** `{days: [{date, total_hours, entries}], week_total_hours, target_hours, progress_percent}`

### `get_week_total`

```
watch.api.time_entry.get_week_total
```

| Parameter | Type | Default |
|-----------|------|---------|
| `date` | string | today |

Lightweight endpoint returning just the total for the current week.

**Returns:** `{total_hours, total_seconds}`

### `duplicate_entry`

```
watch.api.time_entry.duplicate_entry
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entry_name` | string | | Source entry to duplicate |
| `date` | string | today | Date for the new entry |

**Returns:** new Watch Entry dict

### `bulk_duplicate`

```
watch.api.time_entry.bulk_duplicate
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry_names` | list | Source entries to duplicate |
| `date` | string | Target date |

**Returns:** `{created: [...], failed: [...]}`

### `check_yesterday_empty`

```
watch.api.time_entry.check_yesterday_empty
```

Checks whether the user logged any time yesterday (respecting work days).

**Returns:** `{empty: bool, date: string}`

### `get_weekly_chart_data`

```
watch.api.time_entry.get_weekly_chart_data
```

| Parameter | Type | Default |
|-----------|------|---------|
| `date` | string | today |

**Returns:** `{labels: [...], datasets: [{name, values}]}`

### `export_csv`

```
watch.api.time_entry.export_csv
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_date` | string | *(required)* | Start date |
| `to_date` | string | *(required)* | End date |
| `user` | string | current user | |
| `tags` | list | `None` | Filter by tags |
| `entry_type` | string | `None` | Filter by type |

**Returns:** CSV file download

### `bulk_add_tag`

```
watch.api.time_entry.bulk_add_tag
```

| Parameter | Type |
|-----------|------|
| `entry_names` | list |
| `tag` | string |

**Returns:** `{updated: int}`

### `bulk_set_entry_type`

```
watch.api.time_entry.bulk_set_entry_type
```

| Parameter | Type |
|-----------|------|
| `entry_names` | list |
| `entry_type` | string |

**Returns:** `{updated: int}`

### `bulk_delete`

```
watch.api.time_entry.bulk_delete
```

| Parameter | Type |
|-----------|------|
| `entry_names` | list |

**Returns:** `{deleted: int, failed: [...]}`

---

## Tags

### `get_tags`

```
watch.api.tags.get_tags
```

| Parameter | Type | Default |
|-----------|------|---------|
| `include_archived` | bool | `False` |

**Returns:** `[{name, label, color, archived, usage_count}, ...]`

### `create_tag`

```
watch.api.tags.create_tag
```

| Parameter | Type | Default |
|-----------|------|---------|
| `label` | string | *(required)* |
| `color` | string | `None` |

**Returns:** Watch Tag dict

### `update_tag`

```
watch.api.tags.update_tag
```

| Parameter | Type |
|-----------|------|
| `tag_name` | string |
| `label` | string |
| `color` | string |

**Returns:** updated Watch Tag dict

### `rename_tag`

```
watch.api.tags.rename_tag
```

| Parameter | Type |
|-----------|------|
| `tag_name` | string |
| `new_label` | string |

**Returns:** `{name, label}`

### `merge_tag`

```
watch.api.tags.merge_tag
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `source_tag` | string | Tag to merge from (will be deleted) |
| `target_tag` | string | Tag to merge into |

Moves all entry associations from source to target, then deletes source.

**Returns:** `{merged: int, target: tag_name}`

### `archive_tag`

```
watch.api.tags.archive_tag
```

| Parameter | Type |
|-----------|------|
| `tag_name` | string |

Archived tags are hidden from pickers but preserved on existing entries.

**Returns:** `{archived: true}`

### `delete_tag`

```
watch.api.tags.delete_tag
```

| Parameter | Type |
|-----------|------|
| `tag_name` | string |

Permanently deletes the tag and removes all entry associations.

**Returns:** `{deleted: tag_name}`

### `get_tag_stats`

```
watch.api.tags.get_tag_stats
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tag_name` | string | *(required)* |
| `period` | string | `"monthly"` |

**Returns:** `{total_hours, entry_count, by_period: [{period, hours}]}`

### `search_tags`

```
watch.api.tags.search_tags
```

| Parameter | Type | Default |
|-----------|------|---------|
| `query` | string | `""` |
| `limit` | int | `10` |

**Returns:** `[{name, label, color}, ...]`

### `get_budget_usage`

```
watch.api.tags.get_budget_usage
```

| Parameter | Type | Default |
|-----------|------|---------|
| `tag_name` | string | *(required)* |
| `period` | string | `None` |

**Returns:** `{budget_hours, used_hours, remaining_hours, usage_percent, period_start, period_end}`

### `get_all_budgets`

```
watch.api.tags.get_all_budgets
```

**Returns:** `[{tag_name, tag_label, budget_hours, used_hours, usage_percent, status}, ...]`

---

## Search

### `search_entries`

```
watch.api.search.search_entries
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | Search term |
| `limit` | int | `10` | |
| `from_date` | string | `None` | |
| `to_date` | string | `None` | |
| `tags` | list | `None` | |
| `entry_type` | string | `None` | |

**Returns:** `[{name, context_label, date, duration, entry_type, tags}, ...]`

### `search_tags`

```
watch.api.search.search_tags
```

| Parameter | Type | Default |
|-----------|------|---------|
| `query` | string | *(required)* |
| `limit` | int | `10` |

**Returns:** `[{name, label, color, usage_count}, ...]`

### `timer_action`

```
watch.api.search.timer_action
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | `start`, `stop`, `pause`, or `resume` |

Convenience method for Dock global search to trigger timer actions.

**Returns:** timer state dict

### `navigation_shortcuts`

```
watch.api.search.navigation_shortcuts
```

| Parameter | Type | Default |
|-----------|------|---------|
| `query` | string | `""` |

**Returns:** `[{label, route, icon}, ...]` — matching Watch navigation targets.

---

## User Settings

### `get_preferences`

```
watch.api.user_settings.get_preferences
```

**Returns:** `{weekly_hour_target, keyboard_shortcuts_enabled, pomodoro_work_minutes, pomodoro_break_minutes, pomodoro_sessions, extension_token_set}`

### `save_preferences`

```
watch.api.user_settings.save_preferences
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `**fields` | any | Any valid Watch User Settings field |

**Returns:** updated preferences dict

### `generate_extension_token`

```
watch.api.user_settings.generate_extension_token
```

Generates a new API token for the browser extension. Revokes any existing token.

**Returns:** `{token: string}`

### `revoke_extension_token`

```
watch.api.user_settings.revoke_extension_token
```

**Returns:** `{revoked: true}`

---

## Settings

### `get_settings`

```
watch.api.settings.get_settings
```

**Returns:** full Watch Settings dict (System Manager only for sensitive fields; Time Trackers receive a filtered subset).

### `get_work_days`

```
watch.api.settings.get_work_days
```

**Returns:** `{monday, tuesday, wednesday, thursday, friday, saturday, sunday}` — each a boolean.

### `save_settings`

```
watch.api.settings.save_settings
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `**fields` | any | Any valid Watch Settings field |

System Manager only.

**Returns:** updated Watch Settings dict

---

## Templates

### `get_favorites`

```
watch.api.templates.get_favorites
```

**Returns:** `[{name, label, entry_type, tags, context_label, sort_order}, ...]` — user's favorite templates sorted by `sort_order`.

### `get_day_templates`

```
watch.api.templates.get_day_templates
```

**Returns:** `[{name, label, items: [{context_label, entry_type, duration, tags}]}, ...]`

### `save_from_entry`

```
watch.api.templates.save_from_entry
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entry_name` | string | *(required)* | Watch Entry to save as template |
| `label` | string | `None` | Template label (defaults to entry's context_label) |
| `favorite` | bool | `False` | Add to favorites |

**Returns:** Watch Entry Template dict

### `save_day_template`

```
watch.api.templates.save_day_template
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | string | Template name |
| `items` | list | `[{context_label, entry_type, duration, tags}]` |

**Returns:** Watch Entry Template dict

### `apply_day_template`

```
watch.api.templates.apply_day_template
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `template_name` | string | *(required)* | |
| `date` | string | today | Target date |

Creates entries for all items in the template.

**Returns:** `{created: [...], total_hours}`

### `delete_template`

```
watch.api.templates.delete_template
```

| Parameter | Type |
|-----------|------|
| `template_name` | string |

**Returns:** `{deleted: template_name}`

### `update_template`

```
watch.api.templates.update_template
```

| Parameter | Type |
|-----------|------|
| `template_name` | string |
| `**fields` | any |

**Returns:** updated template dict

### `reorder_favorites`

```
watch.api.templates.reorder_favorites
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `ordered_names` | list | Template names in desired order |

**Returns:** `{reordered: int}`

---

## Billing

### `get_summary`

```
watch.api.billing.get_summary
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_date` | string | *(required)* | |
| `to_date` | string | *(required)* | |
| `tags` | list | `None` | Filter by tags |
| `contact` | string | `None` | Filter by contact |
| `entry_type` | string | `"billable"` | |

**Returns:** `{entries: [...], total_hours, total_amount, by_tag: [{tag, hours, amount}], by_contact: [{contact, hours}]}`

### `mark_sent`

```
watch.api.billing.mark_sent
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry_names` | list | Entries to mark as invoiced |
| `reference` | string | Invoice or reference number |

**Returns:** `{marked: int}`

### `get_billing_actions`

```
watch.api.billing.get_billing_actions
```

**Returns:** `[{label, action, app, icon}, ...]` — available billing actions from apps declaring `watch_billing_actions`.

### `forward_to_app`

```
watch.api.billing.forward_to_app
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | string | Target app name |
| `action` | string | Action identifier |
| `entry_names` | list | Entries to forward |
| `from_date` | string | |
| `to_date` | string | |

Forwards billing data to an external invoicing app.

**Returns:** app-specific response

### `export_csv`

```
watch.api.billing.export_csv
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_date` | string | *(required)* | |
| `to_date` | string | *(required)* | |
| `tags` | list | `None` | |
| `contact` | string | `None` | |
| `entry_type` | string | `"billable"` | |

**Returns:** CSV file download with billing-formatted columns.

---

## Integrations

### `test_slack`

```
watch.api.integrations.test_slack
```

Sends a test message to the configured Slack webhook.

**Returns:** `{success: bool, error?: string}`

### `test_linear`

```
watch.api.integrations.test_linear
```

Tests the Linear API connection.

**Returns:** `{success: bool, team_name?: string, error?: string}`

### `search_linear_issues`

```
watch.api.integrations.search_linear_issues
```

| Parameter | Type | Default |
|-----------|------|---------|
| `query` | string | *(required)* |
| `limit` | int | `10` |

**Returns:** `[{id, identifier, title, state, url}, ...]`

### `test_github`

```
watch.api.integrations.test_github
```

Tests the GitHub API connection.

**Returns:** `{success: bool, user?: string, error?: string}`

### `search_github_issues`

```
watch.api.integrations.search_github_issues
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *(required)* | Search term |
| `repo` | string | `None` | Override default repo |
| `limit` | int | `10` | |

**Returns:** `[{number, title, state, url, labels}, ...]`

---

## ERPNext Bridge

All methods require ERPNext to be installed and `erpnext_sync_enabled` to be active. Returns `{error: "ERPNext sync not enabled"}` otherwise.

### `sync_day`

```
watch.api.erpnext_bridge.sync_day
```

| Parameter | Type | Default |
|-----------|------|---------|
| `date` | string | today |
| `user` | string | current user |

Syncs all entries for the given date to ERPNext Timesheets.

**Returns:** `{synced: int, skipped: int, errors: [...]}`

### `sync_entry`

```
watch.api.erpnext_bridge.sync_entry
```

| Parameter | Type |
|-----------|------|
| `entry_name` | string |

**Returns:** `{synced: bool, timesheet_name?: string, error?: string}`

### `bulk_sync`

```
watch.api.erpnext_bridge.bulk_sync
```

| Parameter | Type |
|-----------|------|
| `entry_names` | list |

**Returns:** `{synced: int, failed: int, errors: [...]}`

### `get_sync_status`

```
watch.api.erpnext_bridge.get_sync_status
```

| Parameter | Type | Default |
|-----------|------|---------|
| `from_date` | string | `None` |
| `to_date` | string | `None` |

**Returns:** `{total_entries, synced, unsynced, last_sync_at}`

### `test_connection`

```
watch.api.erpnext_bridge.test_connection
```

Tests that ERPNext is reachable and the Activity Type exists.

**Returns:** `{success: bool, erpnext_version?: string, activity_type_exists?: bool, error?: string}`
