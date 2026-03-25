# Hook Integration

Watch integrates with Dock by declaring hooks in `watch/hooks.py`. Dock reads these at runtime — Watch never imports Dock code directly.

---

## `dock_app_registry`

Registers Watch in the Dock app switcher.

```python
dock_app_registry = {
    "label": "Watch",
    "icon": "clock",
    "color": "#F59E0B",
    "route": "/watch",
}
```

---

## `dock_timer_api`

Exposes 5 endpoints that Dock calls to render the timer widget in the top bar.

```python
dock_timer_api = {
    "get_state": "watch.api.timer.get_timer_state",
    "start": "watch.api.timer.start_timer",
    "pause": "watch.api.timer.pause_timer",
    "resume": "watch.api.timer.resume_timer",
    "stop": "watch.api.timer.stop_timer",
}
```

Dock calls `get_state` during boot to populate `frappe.boot.dock.timer_state`. The top bar widget then calls `start`, `pause`, `resume`, and `stop` as the user interacts with it.

---

## `dock_search_sections`

Registers 4 search sections in Dock Global Search (Cmd+K).

```python
dock_search_sections = [
    {
        "label": "Time Entries",
        "doctype": "Watch Entry",
        "search_fields": ["context_label", "description"],
        "route_field": "name",
        "route_prefix": "/watch/entry/",
    },
    {
        "label": "Tags",
        "doctype": "Watch Tag",
        "search_fields": ["label"],
        "route_field": "name",
        "route_prefix": "/watch/tags/",
    },
    {
        "label": "Start Timer",
        "type": "action",
        "handler": "watch.api.search.timer_action",
    },
    {
        "label": "Navigate",
        "type": "shortcut",
        "handler": "watch.api.search.navigation_shortcuts",
    },
]
```

The first two sections are DocType-based searches. "Start Timer" is an action section that lets users start/stop the timer from global search. "Navigate" provides shortcuts to Watch pages (Today, Week, Reports, Tags, Billing).

---

## `dock_settings_sections`

Registers the Watch settings panel inside Dock Settings. The settings UI is delivered as an ESM bundle that Dock lazy-loads.

```python
dock_settings_sections = [
    {
        "app": "watch",
        "label": "Watch",
        "icon": "clock",
        "esm_bundle": "/assets/watch/js/watch-settings.esm.js",
        "subsections": [
            {"key": "general", "label": "General"},
            {"key": "work_days", "label": "Work Days"},
            {"key": "budgets", "label": "Budgets"},
            {"key": "integrations", "label": "Integrations"},
            {"key": "erpnext", "label": "ERPNext Bridge"},
        ],
    },
]
```

---

## `dock_bridges`

Registers the ERPNext Timesheet sync bridge. Dock displays bridge status and allows manual sync triggers from the settings panel.

```python
dock_bridges = [
    {
        "label": "ERPNext Timesheet Sync",
        "target_app": "erpnext",
        "source_doctype": "Watch Entry",
        "direction": "push",
        "status_endpoint": "watch.api.erpnext_bridge.get_sync_status",
        "sync_endpoint": "watch.api.erpnext_bridge.sync_day",
        "settings_route": "/watch/settings/erpnext",
    },
]
```

---

## `dock_activity_sources`

Registers Watch Entry as a source for the Dock activity feed.

```python
dock_activity_sources = [
    {
        "doctype": "Watch Entry",
        "label": "Time Entry",
        "icon": "clock",
        "fields": ["context_label", "duration", "entry_type", "date"],
        "activity_types": ["create", "update"],
    },
]
```

---

## `dock_notification_types`

Registers two notification types that Watch can publish via Dock's notification system.

```python
dock_notification_types = [
    {
        "type": "budget_warning",
        "label": "Budget Warning",
        "icon": "alert-triangle",
        "description": "Tag budget approaching limit",
    },
    {
        "type": "budget_exceeded",
        "label": "Budget Exceeded",
        "icon": "alert-circle",
        "description": "Tag budget has been exceeded",
    },
]
```

---

## `watch_billing_actions`

An extensibility hook that Watch itself publishes. Other apps (e.g., an invoicing app) can declare `watch_billing_actions` in their own `hooks.py` to add actions to the Watch billing panel.

```python
# Example: in another app's hooks.py
watch_billing_actions = [
    {
        "label": "Create Invoice",
        "action": "create_invoice",
        "icon": "file-text",
        "endpoint": "invoicing.api.create_from_watch",
    },
]
```

Watch reads these hooks via `frappe.get_hooks("watch_billing_actions")` and surfaces them in the billing UI.

---

## `watch_event_hooks`

Event listeners that Watch fires at key moments. Other apps can register handlers.

```python
# Example: in another app's hooks.py
watch_event_hooks = {
    "on_entry_create": "myapp.handlers.on_watch_entry_create",
    "on_entry_update": "myapp.handlers.on_watch_entry_update",
    "on_timer_start": "myapp.handlers.on_timer_start",
    "on_timer_stop": "myapp.handlers.on_timer_stop",
}
```

Watch calls `frappe.get_hooks("watch_event_hooks")` and invokes registered handlers for each event type. Handlers receive the relevant document as a dict argument.
