# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Tonic

"""Jana Daily Briefing source — Watch time tracking data."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate


@frappe.whitelist()
def get_briefing(date: str | None = None) -> dict:
	"""Return a briefing summary of the user's time tracking data.

	Includes yesterday's tracked time, active timers, and budget alerts.
	"""
	today = getdate(date or nowdate())
	yesterday = add_days(today, -1)

	return {
		"yesterday": _get_daily_summary(yesterday),
		"active_timer": _get_active_timer(),
		"budget_alerts": _get_budget_alerts(),
	}


def _get_daily_summary(date) -> dict:
	"""Summarise tracked time for a given date."""
	entries = frappe.get_all(
		"Watch Entry",
		filters={
			"owner": frappe.session.user,
			"date": date,
		},
		fields=["duration_hours", "entry_type", "description"],
		order_by="creation asc",
		limit_page_length=50,
	)

	total_hours = sum(e.duration_hours or 0 for e in entries)
	billable_hours = sum(
		e.duration_hours or 0 for e in entries if e.entry_type == "Billable"
	)

	return {
		"date": str(date),
		"total_hours": round(total_hours, 2),
		"billable_hours": round(billable_hours, 2),
		"entry_count": len(entries),
	}


def _get_active_timer() -> dict | None:
	"""Return the current user's active timer, if any."""
	timers = frappe.get_all(
		"Watch Timer",
		filters={"user": frappe.session.user},
		fields=["name", "state", "description", "accumulated_seconds"],
		limit_page_length=1,
	)

	if not timers:
		return None

	timer = timers[0]
	if timer.state not in ("running", "paused"):
		return None

	return {
		"status": timer.state,
		"description": timer.description or "",
		"accumulated_seconds": timer.accumulated_seconds or 0,
	}


def _get_budget_alerts() -> list[dict]:
	"""Return tags where budget usage exceeds 80%."""
	tags = frappe.get_all(
		"Watch Tag",
		filters={
			"owner": frappe.session.user,
			"monthly_hour_budget": [">", 0],
		},
		fields=["tag_name", "monthly_hour_budget"],
		limit_page_length=50,
	)

	alerts = []
	for tag in tags:
		# Get current month's usage via the child table Watch Entry Tag
		usage = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(we.duration_hours), 0) as used
			FROM `tabWatch Entry` we
			INNER JOIN `tabWatch Entry Tag` wet ON wet.parent = we.name
			WHERE we.owner = %(user)s
			  AND MONTH(we.date) = MONTH(CURDATE())
			  AND YEAR(we.date) = YEAR(CURDATE())
			  AND wet.tag = %(tag_name)s
			""",
			{"user": frappe.session.user, "tag_name": tag.tag_name},
			as_dict=True,
		)

		used = usage[0].used if usage else 0
		budget = tag.monthly_hour_budget
		pct = round((used / budget) * 100, 1) if budget else 0

		if pct >= 80:
			alerts.append({
				"tag": tag.tag_name,
				"budget_hours": budget,
				"used_hours": round(used, 2),
				"usage_percent": pct,
			})

	return alerts
