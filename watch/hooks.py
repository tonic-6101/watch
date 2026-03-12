# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

app_name = "watch"
app_title = "Watch"
app_publisher = "Tonic"
app_description = "Standalone time tracking for Frappe"
app_email = "hello@tonic.to"
app_license = "agpl-3.0"
app_logo_url = "/assets/watch/images/logo.svg"

# --------------------------------------------------
# Dock ecosystem integration
# --------------------------------------------------

# Dock top-bar timer widget calls these endpoints
dock_timer_api = {
	"start": "watch.api.timer.start_timer",
	"stop": "watch.api.timer.stop_timer",
	"pause": "watch.api.timer.pause_timer",
	"resume": "watch.api.timer.resume_timer",
	"status": "watch.api.timer.get_timer_state",
}

# Registers Watch in Dock's app switcher and top-bar label
dock_app_registry = {
	"label": "Watch",
	"icon": "/assets/watch/images/logo.svg",
	"color": "#6366f1",
	"route": "/watch",
}

# Search sections contributed to Dock's global search (Feature 12)
dock_search_sections = [
	{
		"label": "Time Entries",
		"endpoint": "watch.api.search.search_entries",
		"icon": "clock",
		"app": "watch",
		"order": 10,
	},
	{
		"label": "Tags",
		"endpoint": "watch.api.search.search_tags",
		"icon": "tag",
		"app": "watch",
		"order": 20,
	},
	{
		"label": "Start Timer",
		"endpoint": "watch.api.search.timer_action",
		"icon": "play",
		"app": "watch",
		"order": 30,
	},
	{
		"label": "Navigate",
		"endpoint": "watch.api.search.navigation_shortcuts",
		"icon": "navigation",
		"app": "watch",
		"order": 40,
	},
]

# --------------------------------------------------
# Extensibility hooks (other apps implement these)
# --------------------------------------------------

# Billing bridge — invoicing apps register forwarding targets here.
#
# Each entry must be a dict with:
#   app      (str)  — app name as registered in Frappe (filtered to installed apps at runtime)
#   label    (str)  — button label shown in Watch UI ("Prepare Draft in Micro", "Send to …")
#   endpoint (str)  — dotted Python path called by watch.api.billing.forward_to_app
#   icon     (str)  — lucide icon name (optional, used for future icon rendering)
#
# SIF compliance: labels must use neutral forwarding language.
# Never use "Invoice", "Rechnung", "Factura" or similar in the label —
# that wording belongs on the invoicing app side only.
#
# The endpoint receives a structured payload (see spec/features/09-forward-bridge.md).
# It may return {"draft_url": "..."} to show a link in Watch after forwarding.
#
# Example (in your app's hooks.py):
#   watch_billing_actions = [
#       {
#           "app":      "micro",
#           "label":    "Prepare Draft in Micro",
#           "endpoint": "micro.api.billing.create_from_time_entries",
#           "icon":     "file-text",
#       }
#   ]
#
# watch_billing_actions = []

# Event hooks: other apps can listen to watch events
watch_event_hooks = []

# --------------------------------------------------
# Scheduled tasks
# --------------------------------------------------

scheduler_events = {
	"daily": [
		"watch.tasks.auto_stop_forgotten_timers",
	],
	"hourly": [
		"watch.tasks.sync_to_erpnext_scheduled",
	],
}

# --------------------------------------------------
# Vue SPA entry point
# --------------------------------------------------

website_route_rules = [
	{"from_route": "/watch/<path:subpath>", "to_route": "watch"},
	{"from_route": "/watch", "to_route": "watch"},
]

# --------------------------------------------------
# User data (GDPR)
# --------------------------------------------------

user_data_fields = [
	{
		"doctype": "FT Time Entry",
		"filter_by": "user",
		"redact_fields": ["description"],
		"partial": 1,
	},
	{
		"doctype": "FT Timer",
		"filter_by": "user",
		"partial": 1,
	},
	{
		"doctype": "FT User Settings",
		"filter_by": "user",
		"partial": 1,
	},
]

# --------------------------------------------------
# Installation
# --------------------------------------------------

after_install = "watch.install.after_install"
after_uninstall = "watch.uninstall.after_uninstall"
