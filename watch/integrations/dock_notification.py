# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Dock Notification integration — publishes Watch events to Dock's bell icon.

Uses dock.api.notifications.publish() which validates notification_type
against dock_notification_types declared in watch/hooks.py, creates a
Dock Notification record, and pushes a realtime event to the recipient.
"""

import frappe
from frappe import _

# Route templates for deep-linking from Dock bell -> Watch SPA
_ROUTE_MAP = {
	"Watch Entry": "/watch/entries/{name}",
	"Watch Tag": "/watch/tags",
}


def _dock_installed() -> bool:
	return "dock" in frappe.get_installed_apps()


def _build_action_url(reference_doctype: str, reference_name: str) -> str:
	"""Build a deep-link URL for the Dock notification."""
	template = _ROUTE_MAP.get(reference_doctype)
	if not template or not reference_name:
		return ""
	return template.format(name=reference_name)


def publish(
	notification_type: str,
	title: str,
	for_user: str,
	message: str = None,
	reference_doctype: str = None,
	reference_name: str = None,
):
	"""
	Publish a notification to Dock's bell icon.

	Safe to call when Dock is not installed — silently returns.
	Failures are logged but never break the calling code.
	"""
	if not _dock_installed():
		return

	action_url = _build_action_url(reference_doctype, reference_name)

	try:
		from dock.api.notifications import publish as dock_publish
		dock_publish(
			for_user=for_user,
			from_app="watch",
			notification_type=notification_type,
			title=title,
			message=message,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			action_url=action_url,
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Watch: failed to publish Dock notification",
		)


# ------------------------------------------------------------------
# Timer events
# ------------------------------------------------------------------

def on_timer_auto_stopped(entry_name: str, user: str, threshold_hours: float):
	"""Notify when a forgotten timer is auto-stopped by the scheduler."""
	entry = frappe.db.get_value(
		"Watch Entry", entry_name, ["description", "duration_hours"], as_dict=True
	)
	if not entry:
		return

	desc = entry.description or _("Untitled entry")
	publish(
		notification_type="timer_auto_stopped",
		title=_("Timer auto-stopped: {0}").format(desc[:60]),
		for_user=user,
		message=_("Your timer ran for over {0}h and was automatically stopped.").format(
			int(threshold_hours)
		),
		reference_doctype="Watch Entry",
		reference_name=entry_name,
	)


# ------------------------------------------------------------------
# Focus / Pomodoro events
# ------------------------------------------------------------------

def on_focus_completed(user: str, sessions_completed: int, total_minutes: float):
	"""Notify when all pomodoro sessions are completed."""
	publish(
		notification_type="focus_completed",
		title=_("Focus run completed: {0} sessions").format(sessions_completed),
		for_user=user,
		message=_("{0} sessions totalling {1} minutes of focused work.").format(
			sessions_completed, int(total_minutes)
		),
	)


# ------------------------------------------------------------------
# Billing bridge events
# ------------------------------------------------------------------

def on_entries_forwarded(user: str, app_label: str, count: int, total_hours: float):
	"""Notify when time entries are forwarded to an invoicing app."""
	publish(
		notification_type="entries_forwarded",
		title=_("{0} entries forwarded to {1}").format(count, app_label),
		for_user=user,
		message=_("{0} entries ({1}h) sent for invoicing.").format(
			count, round(total_hours, 1)
		),
	)


def on_forwarding_failed(user: str, app_label: str, error: str):
	"""Notify when billing forwarding fails."""
	publish(
		notification_type="forwarding_failed",
		title=_("Failed to forward entries to {0}").format(app_label),
		for_user=user,
		message=_("Error: {0}").format(error[:200]),
	)


# ------------------------------------------------------------------
# ERPNext bridge events
# ------------------------------------------------------------------

def on_erpnext_sync_failed(error: str):
	"""Notify System Managers when ERPNext sync fails."""
	managers = frappe.get_all(
		"Has Role",
		filters={"role": "System Manager", "parenttype": "User"},
		pluck="parent",
	)
	for user in set(managers):
		publish(
			notification_type="erpnext_sync_failed",
			title=_("ERPNext sync failed"),
			for_user=user,
			message=_("Error: {0}").format(error[:200]),
		)
