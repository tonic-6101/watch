# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


def is_bridge_active() -> bool:
	if "erpnext" not in frappe.get_installed_apps():
		return False
	settings = frappe.get_single("Watch Settings")
	return bool(settings.enable_erpnext_bridge)


def _get_employee(user: str) -> str | None:
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		frappe.log_error(
			f"No ERPNext Employee found for user {user}",
			"Watch ERPNext Bridge",
		)
	return employee


def _get_day_entries(user: str, date: str) -> list:
	"""Return all non-running Watch Entry records for user+date."""
	settings = frappe.get_single("Watch Settings")
	filters = {"user": user, "date": date, "is_running": 0}
	if settings.sync_billable_only:
		filters["entry_type"] = "billable"
	return frappe.get_all(
		"Watch Entry",
		filters=filters,
		fields=[
			"name", "date", "start_time", "end_time",
			"duration_hours", "description", "entry_type",
		],
		order_by="start_time asc",
	)


def _resolve_project_tag(entry_name: str) -> tuple:
	"""Return (project_name, task_name) by matching Watch Tag category to ERPNext docs."""
	tag_rows = frappe.get_all(
		"Watch Entry Tag",
		filters={"parent": entry_name},
		fields=["tag_name", "tag_category"],
	)
	project = None
	task = None
	for tag in tag_rows:
		cat = tag.get("tag_category") or ""
		name = tag.get("tag_name") or ""
		if cat == "Project" and not project:
			project = frappe.db.get_value("Project", {"project_name": name}, "name")
		elif cat == "Task" and not task:
			task = frappe.db.get_value("Task", {"subject": name}, "name")
	return project, task


@frappe.whitelist()
def sync_day(date: str, user: str = None) -> dict:
	"""Sync all entries for a user on a given date into one ERPNext Timesheet.

	On re-sync: deletes and recreates the draft Timesheet for that day.
	Blocks if the Timesheet is already submitted.
	"""
	if not is_bridge_active():
		return {"skipped": True, "reason": "bridge inactive"}

	if not user:
		user = frappe.session.user

	settings = frappe.get_single("Watch Settings")
	employee = _get_employee(user)
	if not employee:
		return {"skipped": True, "reason": f"no Employee record for {user}"}

	entries = _get_day_entries(user, date)
	if not entries:
		return {"skipped": True, "reason": "no entries for this day"}

	# Check for existing Timesheet
	existing = frappe.db.get_value(
		"Timesheet",
		{"employee": employee, "start_date": date, "end_date": date},
		["name", "docstatus"],
		as_dict=True,
	)

	if existing:
		if existing.docstatus == 1:
			error_msg = _(
				"ERPNext Timesheet {0} for {1} is submitted — re-sync blocked."
			).format(existing.name, date)
			frappe.db.set_single_value("Watch Settings", "last_sync_error", error_msg)
			frappe.log_error(error_msg, "Watch ERPNext Bridge")
			return {"error": error_msg}
		frappe.delete_doc("Timesheet", existing.name, ignore_permissions=True)

	# Build Timesheet Detail rows
	details = []
	for entry in entries:
		row = {
			"activity_type": settings.default_activity_type or "",
			"from_time": f"{date} {entry.start_time}" if entry.start_time else None,
			"to_time": f"{date} {entry.end_time}" if entry.end_time else None,
			"hours": entry.duration_hours or 0,
			"description": entry.description or "",
			"is_billable": 1 if entry.entry_type == "billable" else 0,
		}
		if settings.map_project_tags:
			project, task = _resolve_project_tag(entry.name)
			if project:
				row["project"] = project
			if task:
				row["task"] = task
		details.append(row)

	ts = frappe.new_doc("Timesheet")
	ts.employee = employee
	ts.start_date = date
	ts.end_date = date
	for d in details:
		ts.append("time_logs", d)
	ts.insert(ignore_permissions=True)

	# Mark entries synced
	for entry in entries:
		frappe.db.set_value(
			"Watch Entry",
			entry.name,
			{"erpnext_synced": 1, "erpnext_timesheet": ts.name},
			update_modified=False,
		)

	frappe.db.set_single_value("Watch Settings", "last_sync_error", "")
	return {"timesheet": ts.name, "entries_synced": len(entries)}


@frappe.whitelist()
def sync_entry(entry_name: str) -> dict:
	"""Sync the day that contains this entry."""
	if not is_bridge_active():
		return {"skipped": True, "reason": "bridge inactive"}

	entry = frappe.get_doc("Watch Entry", entry_name)
	if entry.is_running:
		return {"skipped": True, "reason": "entry is still running"}

	return sync_day(str(entry.date), entry.user)


@frappe.whitelist()
def bulk_sync() -> dict:
	"""Sync all unsynced entries. Called by the manual button or scheduler."""
	if not is_bridge_active():
		return {"skipped": True, "reason": "bridge inactive"}

	# Collect distinct user+date pairs that have unsynced entries
	unsynced = frappe.get_all(
		"Watch Entry",
		filters={"erpnext_synced": 0, "is_running": 0},
		fields=["user", "date"],
		distinct=True,
	)

	synced_days = 0
	errors = []
	for row in unsynced:
		result = sync_day(str(row.date), row.user)
		if result.get("error"):
			errors.append(result["error"])
		elif not result.get("skipped"):
			synced_days += 1

	frappe.db.set_single_value("Watch Settings", "last_bulk_sync", frappe.utils.now_datetime())
	if errors:
		frappe.db.set_single_value("Watch Settings", "last_sync_error", "; ".join(errors[:5]))
	else:
		frappe.db.set_single_value("Watch Settings", "last_sync_error", "")

	return {"days_synced": synced_days, "errors": errors}


@frappe.whitelist()
def get_sync_status() -> dict:
	"""Bridge status for Dock's Integrations dashboard."""
	if not is_bridge_active():
		return {"active": False, "reason": _("Bridge disabled or ERPNext not installed")}

	settings = frappe.get_single("Watch Settings")
	unsynced = frappe.db.count("Watch Entry", {"erpnext_synced": 0, "is_running": 0})
	return {
		"active": True,
		"unsynced_count": unsynced,
		"last_bulk_sync": str(settings.get("last_bulk_sync") or ""),
		"last_error": settings.get("last_sync_error") or None,
	}


@frappe.whitelist()
def test_connection() -> dict:
	"""Verify ERPNext is reachable and Timesheet/Employee DocTypes are accessible."""
	if "erpnext" not in frappe.get_installed_apps():
		return {"ok": False, "error": _("ERPNext is not installed on this site.")}
	try:
		frappe.get_meta("Timesheet")
		frappe.get_meta("Employee")
		return {"ok": True}
	except Exception as e:
		return {"ok": False, "error": str(e)}
