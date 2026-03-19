# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


def auto_stop_forgotten_timers():
	"""Stop timers running past Watch Settings.auto_stop_timer_after hours (0 = disabled)."""
	settings = frappe.get_single("Watch Settings")
	threshold_hours = settings.auto_stop_timer_after or 0
	if not threshold_hours:
		return

	from datetime import datetime, timedelta

	cutoff = datetime.now() - timedelta(hours=threshold_hours)

	running_timers = frappe.get_all(
		"Watch Timer",
		filters={"state": "running", "started_at": ["<", cutoff]},
		fields=["name", "user"],
	)

	for timer_rec in running_timers:
		try:
			# Import here to avoid circular imports
			from watch.api.timer import stop_timer

			frappe.set_user(timer_rec.user)
			result = stop_timer(notes=None)

			# Append auto-stop flag note to the entry description
			entry_name = (result or {}).get("entry", {}).get("name")
			if entry_name:
				entry = frappe.get_doc("Watch Entry", entry_name)
				flag = _("[Auto-stopped after {0}h]").format(threshold_hours)
				entry.description = ((entry.description or "") + "\n" + flag).strip()
				entry.save(ignore_permissions=True)

			frappe.logger().info(f"Auto-stopped timer for {timer_rec.user}")
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Auto-stop failed for {timer_rec.user}")
		finally:
			frappe.set_user("Administrator")


def sync_to_erpnext_scheduled():
	"""Run ERPNext sync when Watch Settings.sync_mode = 'scheduled'.

	Runs every hour but respects sync_interval:
	  - hourly        → always runs
	  - every_6_hours → skips if last_bulk_sync < 6h ago
	  - daily         → skips if last_bulk_sync < 24h ago
	"""
	settings = frappe.get_single("Watch Settings")
	if not settings.enable_erpnext_bridge or settings.sync_mode != "scheduled":
		return

	interval = settings.sync_interval or "hourly"
	if interval != "hourly" and settings.last_bulk_sync:
		from datetime import datetime, timedelta

		min_gap = timedelta(hours=6) if interval == "every_6_hours" else timedelta(hours=24)
		if datetime.now() - settings.last_bulk_sync < min_gap:
			return

	from watch.api.erpnext_bridge import bulk_sync

	bulk_sync()
