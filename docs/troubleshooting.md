# Troubleshooting

## Timer stuck in running state

**Symptom:** The timer shows as running but the user did not start it, or it has been running for an unreasonable duration.

**Cause:** The browser was closed or the user went offline without stopping the timer. If `auto_stop_timer_after` is set to `0` (disabled), the timer runs indefinitely.

**Fix:**

1. Set `auto_stop_timer_after` in Watch Settings to a reasonable value (e.g., `8` hours). A scheduled task will auto-stop stale timers.
2. To manually fix a stuck timer, call `stop_timer_at` with the intended stop time:

```python
import frappe
frappe.call("watch.api.timer.stop_timer_at", stop_time="2026-03-25 18:00:00")
```

3. Or reset the timer state directly:

```python
timer = frappe.get_single("Watch Timer")
timer.state = "stopped"
timer.started_at = None
timer.paused_at = None
timer.save(ignore_permissions=True)
frappe.db.commit()
```

---

## Entries locked — cannot edit

**Symptom:** Attempting to update an entry returns a permission error or "entry is locked" message.

**Cause:** The `lock_entries_older_than` setting in Watch Settings locks entries older than N days. Once locked, only System Managers can edit them.

**Fix:**

- Temporarily set `lock_entries_older_than` to `0` (no locking), edit the entry, then restore the setting.
- Or ask a System Manager to update the entry directly.

---

## ERPNext sync failures

**Symptom:** Entries fail to sync to ERPNext Timesheets. The sync status shows errors.

**Check:**

1. Verify ERPNext is installed: `bench --site your-site list-apps`
2. Verify sync is enabled: `Watch Settings > ERPNext Bridge > erpnext_sync_enabled`
3. Test the connection:

```python
frappe.call("watch.api.erpnext_bridge.test_connection")
```

4. Check that the `erpnext_default_activity_type` exists in ERPNext. If missing, create it under `HR > Activity Type`.
5. Review errors in the Dock sync log (if Dock is installed): `Dock Settings > Bridges > Sync Log`.

**Common errors:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Activity Type not found` | Default activity type doesn't exist in ERPNext | Create the Activity Type in ERPNext |
| `Timesheet validation failed` | ERPNext requires fields Watch doesn't populate | Check ERPNext Timesheet mandatory fields |
| `ERPNext sync not enabled` | Sync flag is off | Enable `erpnext_sync_enabled` in Watch Settings |

---

## Browser extension token not working

**Symptom:** The browser extension cannot connect to Watch.

**Fix:**

1. Generate a new token: call `watch.api.user_settings.generate_extension_token`. This revokes any existing token.
2. Copy the returned token into the extension settings.
3. Ensure the extension is pointed at the correct site URL (including protocol and port).
4. Check that the user has the **Time Tracker** role.

---

## Pomodoro not advancing

**Symptom:** Focus mode starts but does not transition from work to break (or break to next session).

**Cause:** Focus mode transitions are triggered by the frontend polling the timer state. If the browser tab is inactive or the SPA is not loaded, transitions may not fire.

**Fix:**

- Keep the Watch tab active during focus sessions.
- Check that the focus parameters are set correctly (default: 25 min work, 5 min break).
- If the session is stuck, call `end_focus` to stop it cleanly:

```python
frappe.call("watch.api.timer.end_focus")
```

---

## Budget alerts not firing

**Symptom:** Tag budgets are exceeded but no notification appears.

**Check:**

1. Verify budgets are enabled: `Watch Settings > enable_budgets` must be checked.
2. Verify `budget_warning_threshold` is set (default: 80%).
3. Verify the tag has a budget configured (check `budget_hours` on the Watch Tag).
4. Verify Dock is installed — budget notifications are published via `dock_notification_types`. Without Dock, notifications have no delivery mechanism.
5. Check that the user has not muted the `budget_warning` notification type in Dock notification preferences.

---

## Keyboard shortcuts not working

**Symptom:** Pressing keyboard shortcuts (e.g., `S` to start timer) does nothing.

**Check:**

1. Verify shortcuts are enabled in user preferences: `Watch User Settings > keyboard_shortcuts_enabled`
2. Ensure focus is on the Watch SPA (not on an input field or another app's iframe).
3. Check for conflicts with browser extensions that may capture the same key bindings.

---

## Dock timer widget missing

**Symptom:** The timer widget does not appear in the Dock top bar even though Watch is installed.

**Check:**

1. Verify Watch is installed: `bench --site your-site list-apps`
2. Verify `frappe.boot.dock.watch_installed` is `true` in the browser console.
3. Clear cache and reload:

```bash
bench --site your-site clear-cache
```

4. If the boot data shows `watch_installed: false`, check that Watch's `hooks.py` declares `dock_timer_api`. Dock uses this hook to detect Watch.
5. Rebuild assets if hooks were recently changed:

```bash
bench build --app watch
bench build --app dock
```

---

## Watch Settings issingle flag

**Symptom:** Watch Settings or Watch Timer throws "DocType is not a Single" errors after migration.

**Cause:** Known Frappe v16 issue where the `issingle` flag is not preserved during `bench migrate`.

**Fix:**

```python
frappe.db.sql("UPDATE `tabDocType` SET issingle=1 WHERE name='Watch Settings'")
frappe.db.sql("UPDATE `tabDocType` SET issingle=1 WHERE name='Watch Timer'")
frappe.db.sql("UPDATE `tabDocType` SET issingle=1 WHERE name='Watch User Settings'")
frappe.db.commit()
```
