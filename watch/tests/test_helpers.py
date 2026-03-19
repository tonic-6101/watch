# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Shared test utilities for Watch tests."""

import frappe


def ensure_watch_settings():
	"""Ensure Watch Settings singleton exists with sane defaults."""
	if not frappe.db.exists("Watch Settings", "Watch Settings"):
		frappe.get_doc({"doctype": "Watch Settings"}).insert(ignore_permissions=True)


def make_tag(tag_name: str, category: str = None, color: str = None, **kwargs) -> "frappe.Document":
	"""Create an Watch Tag and return the document."""
	if frappe.db.exists("Watch Tag", tag_name):
		return frappe.get_doc("Watch Tag", tag_name)
	tag = frappe.new_doc("Watch Tag")
	tag.tag_name = tag_name
	if category:
		tag.category = category
	if color:
		tag.color = color
	for k, v in kwargs.items():
		tag.set(k, v)
	tag.insert(ignore_permissions=True)
	return tag


def make_entry(
	date: str = None,
	duration_hours: float = 1.0,
	description: str = "Test entry",
	tags: list = None,
	entry_type: str = "billable",
	entry_status: str = "draft",
	user: str = None,
	start_time: str = None,
	end_time: str = None,
	is_running: int = 0,
) -> "frappe.Document":
	"""Create an Watch Entry and return the document."""
	entry = frappe.new_doc("Watch Entry")
	entry.date = date or frappe.utils.today()
	entry.user = user or frappe.session.user
	entry.description = description
	entry.duration_hours = duration_hours
	entry.entry_type = entry_type
	entry.entry_status = entry_status
	entry.is_running = is_running
	if start_time:
		entry.start_time = start_time
	if end_time:
		entry.end_time = end_time
	if not start_time and not end_time:
		entry.flags.keep_duration = True
	if tags:
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})
	entry.insert(ignore_permissions=True)
	return entry


def cleanup_timer(user: str = None):
	"""Reset the Watch Timer for a user to stopped state."""
	user = user or frappe.session.user
	if frappe.db.exists("Watch Timer", user):
		timer = frappe.get_doc("Watch Timer", user)
		timer.state = "stopped"
		timer.accumulated_seconds = 0
		timer.active_entry = None
		timer.description = None
		timer.started_at = None
		timer.paused_at = None
		timer.focus_mode = 0
		timer.focus_phase = "work"
		timer.focus_session_number = 1
		timer.focus_description = None
		timer.save(ignore_permissions=True)
