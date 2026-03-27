# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

from datetime import date, timedelta

import frappe
from frappe import _

from watch.utils.rounding import round_hours, round_hours_in_entry


def _check_soft_lock(entry_date: str):
	"""Throw if the date is older than Watch Settings.lock_entries_older_than days (0 = disabled)."""
	lock_days = int(frappe.db.get_single_value("Watch Settings", "lock_entries_older_than") or 0)
	if lock_days <= 0:
		return
	d = date.fromisoformat(str(entry_date))
	cutoff = date.today() - timedelta(days=lock_days)
	if d < cutoff:
		frappe.throw(_("Entries older than {0} days are locked on this site.").format(lock_days))


def _is_soft_locked(entry_date: str) -> bool:
	"""Return True if the date is older than the lock threshold (no throw)."""
	lock_days = int(frappe.db.get_single_value("Watch Settings", "lock_entries_older_than") or 0)
	if lock_days <= 0:
		return False
	d = date.fromisoformat(str(entry_date))
	cutoff = date.today() - timedelta(days=lock_days)
	return d < cutoff


def _parse_json_list(val) -> list:
	"""Parse a JSON string to list if needed."""
	if isinstance(val, str):
		import json
		return json.loads(val)
	return val or []


def _entry_to_dict(entry) -> dict:
	"""Return entry as dict with tag_names and tag_meta."""
	d = entry.as_dict()
	tag_names = []
	tag_meta = []
	for t in entry.tags:
		name = t.tag_name or t.tag
		tag_names.append(name)
		tag_meta.append({
			"name": t.tag,
			"tag_name": name,
			"color": t.tag_color,
			"category": t.tag_category,
		})
	d["tag_names"] = tag_names
	d["tag_meta"] = tag_meta
	return d


def _serialize_entry(e: dict) -> dict:
	"""Convert non-JSON-serializable values (date, timedelta) to strings."""
	for key in ("date", "start_time", "end_time"):
		val = e.get(key)
		if isinstance(val, timedelta):
			total = int(val.total_seconds())
			h, remainder = divmod(total, 3600)
			m, s = divmod(remainder, 60)
			e[key] = f"{h:02d}:{m:02d}:{s:02d}"
		elif isinstance(val, date):
			e[key] = val.isoformat()
	return e


def _attach_tags(entries: list) -> list:
	"""Attach tag_names and tag_meta to each entry dict from a get_all result."""
	if not entries:
		return entries
	names = [e.name for e in entries]
	tag_rows = frappe.get_all(
		"Watch Entry Tag",
		filters={"parent": ["in", names]},
		fields=["parent", "tag", "tag_name", "tag_color", "tag_category"],
		order_by="idx asc",
	)
	tags_map: dict[str, list] = {}
	meta_map: dict[str, list] = {}
	for row in tag_rows:
		name = row.tag_name or row.tag
		tags_map.setdefault(row.parent, []).append(name)
		meta_map.setdefault(row.parent, []).append({
			"name": row.tag,
			"tag_name": name,
			"color": row.tag_color,
			"category": row.tag_category,
		})
	for e in entries:
		e["tag_names"] = tags_map.get(e.name, [])
		e["tag_meta"]  = meta_map.get(e.name, [])
	return entries


@frappe.whitelist()
def create_entry(
	date: str,
	duration_hours: float = None,
	start_time: str = None,
	end_time: str = None,
	description: str = None,
	entry_type: str = "billable",
	tags: str | list = None,
	linear_issue: str = None,
	github_ref: str = None,
	contact: str = None,
	context_type: str = None,
	context_name: str = None,
) -> dict:
	if tags and isinstance(tags, str):
		import json
		tags = json.loads(tags)

	_check_soft_lock(date)

	entry = frappe.new_doc("Watch Entry")
	entry.date = date
	entry.user = frappe.session.user
	entry.description = description
	entry.entry_type = entry_type or "billable"
	entry.is_running = 0

	if start_time:
		entry.start_time = start_time
	if end_time:
		entry.end_time = end_time
	if duration_hours is not None:
		entry.duration_hours = duration_hours
		if not start_time and not end_time:
			entry.flags.keep_duration = True

	if linear_issue is not None:
		entry.linear_issue = linear_issue
	if github_ref is not None:
		entry.github_ref = github_ref
	if contact:
		entry.contact = contact
	if context_type:
		entry.context_type = context_type
	if context_name:
		entry.context_name = context_name

	if tags:
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})

	entry.insert(ignore_permissions=True)

	try:
		from watch.api.tags import _check_budget_alerts
		_check_budget_alerts(entry)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch budget alert after create")

	return _entry_to_dict(entry)


@frappe.whitelist()
def update_entry(
	entry_name: str,
	date: str = None,
	start_time: str = None,
	end_time: str = None,
	duration_hours: float = None,
	description: str = None,
	entry_type: str = None,
	tags: str | list = None,
	linear_issue: str = None,
	github_ref: str = None,
	contact: str = None,
	context_type: str = None,
	context_name: str = None,
) -> dict:
	entry = frappe.get_doc("Watch Entry", entry_name)

	if entry.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if entry.entry_status == "sent":
		frappe.throw(_("Cannot edit a sent entry"))

	if date is not None:
		_check_soft_lock(date)
		entry.date = date
	else:
		_check_soft_lock(entry.date)
	if start_time is not None:
		entry.start_time = start_time
	if end_time is not None:
		entry.end_time = end_time
	if duration_hours is not None:
		entry.duration_hours = duration_hours
		if start_time is None and end_time is None:
			entry.flags.keep_duration = True
	if description is not None:
		entry.description = description
	if entry_type is not None:
		entry.entry_type = entry_type
	if linear_issue is not None:
		entry.linear_issue = linear_issue
	if github_ref is not None:
		entry.github_ref = github_ref
	if contact is not None:
		entry.contact = contact
	if context_type is not None:
		entry.context_type = context_type
	if context_name is not None:
		entry.context_name = context_name

	if tags is not None:
		if isinstance(tags, str):
			import json
			tags = json.loads(tags)
		entry.set("tags", [])
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})

	entry.save(ignore_permissions=True)

	try:
		from watch.api.tags import _check_budget_alerts
		_check_budget_alerts(entry)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch budget alert after update")

	return _entry_to_dict(entry)


@frappe.whitelist()
def delete_entry(entry_name: str) -> dict:
	entry = frappe.get_doc("Watch Entry", entry_name)

	if entry.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if entry.is_running:
		frappe.throw(_("Cannot delete a running entry — stop the timer first"))

	if entry.entry_status == "sent":
		frappe.throw(_("Cannot delete a sent entry"))

	frappe.delete_doc("Watch Entry", entry_name, ignore_permissions=True)
	return {"deleted": entry_name}


@frappe.whitelist()
def get_daily_summary(date: str) -> dict:
	user = frappe.session.user
	entries = frappe.get_all(
		"Watch Entry",
		filters={"user": user, "date": date, "is_running": 0},
		fields=[
			"name", "date", "start_time", "end_time", "duration_hours",
			"description", "entry_type", "entry_status", "is_running",
			"contact", "context_type", "context_name",
		],
		order_by="start_time asc, creation asc",
	)
	entries = _attach_tags(entries)
	entries = [_serialize_entry(e) for e in entries]

	# Resolve display names for context fields
	from watch.utils.contexts import get_context_display_value
	for e in entries:
		if e.get("contact"):
			e["contact_name"] = frappe.db.get_value("Contact", e["contact"], "full_name") or e["contact"]
		if e.get("context_type") and e.get("context_name"):
			e["context_display"] = get_context_display_value(e["context_type"], e["context_name"]) or e["context_name"]
		round_hours_in_entry(e)

	total_hours = sum(e.get("duration_hours") or 0 for e in entries)
	billable_hours = sum(
		(e.get("duration_hours") or 0)
		for e in entries
		if e.get("entry_type") == "billable"
	)
	rounded_total = sum(e.get("rounded_duration_hours") or 0 for e in entries)
	rounded_billable = sum(
		(e.get("rounded_duration_hours") or 0)
		for e in entries
		if e.get("entry_type") == "billable"
	)

	return {
		"date": date,
		"entries": entries,
		"total_hours": round(total_hours, 4),
		"billable_hours": round(billable_hours, 4),
		"rounded_total_hours": round(rounded_total, 4),
		"rounded_billable_hours": round(rounded_billable, 4),
	}


def _top_tags(day_entries: list, max_chips: int = 3) -> tuple:
	"""Return (top_tags_list, overflow_count) for a day's entries.

	Priority: Client → Project → other categories.
	Deduplicates by tag name; max_chips chips returned.
	"""
	PRIORITY = {"Client": 0, "Project": 1}
	seen: dict[str, dict] = {}  # tag_name → meta dict
	for entry in day_entries:
		for meta in (entry.get("tag_meta") or []):
			name = meta.get("tag_name") or meta.get("name", "")
			if name and name not in seen:
				seen[name] = meta

	ranked = sorted(
		seen.values(),
		key=lambda m: (PRIORITY.get(m.get("category") or "", 2), m.get("tag_name", "")),
	)
	overflow = max(0, len(ranked) - max_chips)
	return ranked[:max_chips], overflow


@frappe.whitelist()
def get_weekly_summary(week_start: str) -> dict:
	"""week_start: ISO date of Monday."""
	user = frappe.session.user
	from datetime import date as date_type

	monday = date_type.fromisoformat(week_start)
	sunday = monday + timedelta(days=6)

	entries = frappe.get_all(
		"Watch Entry",
		filters={
			"user": user,
			"date": ["between", [str(monday), str(sunday)]],
		},
		fields=[
			"name", "date", "start_time", "end_time", "duration_hours",
			"description", "entry_type", "entry_status", "is_running",
		],
		order_by="date asc, start_time asc",
	)
	entries = _attach_tags(entries)

	# Group by day
	days_map: dict[str, list] = {}
	for i in range(7):
		day_str = str(monday + timedelta(days=i))
		days_map[day_str] = []
	for e in entries:
		days_map.setdefault(str(e.date), []).append(e)

	days = []
	for day_str, day_entries in days_map.items():
		day_total = sum(e.get("duration_hours") or 0 for e in day_entries)
		day_billable = sum(
			(e.get("duration_hours") or 0)
			for e in day_entries
			if e.get("entry_type") == "billable"
		)
		day_rounded_total = sum(round_hours(e.get("duration_hours") or 0) for e in day_entries)
		day_rounded_billable = sum(
			round_hours(e.get("duration_hours") or 0)
			for e in day_entries
			if e.get("entry_type") == "billable"
		)
		top, overflow = _top_tags(day_entries)
		days.append({
			"date": day_str,
			"total_hours": round(day_total, 4),
			"billable_hours": round(day_billable, 4),
			"rounded_total_hours": round(day_rounded_total, 4),
			"rounded_billable_hours": round(day_rounded_billable, 4),
			"entry_count": len(day_entries),
			"top_tags": top,
			"overflow_count": overflow,
		})

	total_hours = sum(d["total_hours"] for d in days)
	billable_hours = sum(d["billable_hours"] for d in days)

	# Previous week total for the comparison bar
	prev_monday = monday - timedelta(days=7)
	prev_sunday = prev_monday + timedelta(days=6)
	prev_entries = frappe.get_all(
		"Watch Entry",
		filters={
			"user": user,
			"date": ["between", [str(prev_monday), str(prev_sunday)]],
		},
		fields=["duration_hours"],
	)
	prev_week_total = round(
		sum((e.get("duration_hours") or 0) for e in prev_entries), 4
	)

	# Work days from settings (frontend needs it to know which days to collapse)
	from watch.api.settings import get_work_days
	work_days = get_work_days()

	rounded_total = sum(d["rounded_total_hours"] for d in days)
	rounded_billable = sum(d["rounded_billable_hours"] for d in days)

	return {
		"week_start": str(monday),
		"week_end": str(sunday),
		"days": days,
		"total_hours": round(total_hours, 4),
		"billable_hours": round(billable_hours, 4),
		"rounded_total_hours": round(rounded_total, 4),
		"rounded_billable_hours": round(rounded_billable, 4),
		"prev_week_total_hours": prev_week_total,
		"work_days": work_days,
	}


@frappe.whitelist()
def get_week_total(target_date: str) -> dict:
	"""Return total hours logged in the ISO week containing *target_date*,
	plus the configured work days list.  Lightweight — used by the daily
	view "on track" hint without fetching per-day breakdowns."""
	from datetime import date as date_type
	from watch.api.settings import get_work_days

	user = frappe.session.user
	d = date_type.fromisoformat(target_date)
	monday = d - timedelta(days=d.weekday())
	sunday = monday + timedelta(days=6)

	rows = frappe.get_all(
		"Watch Entry",
		filters={
			"user": user,
			"date": ["between", [str(monday), str(sunday)]],
			"is_running": 0,
		},
		fields=["duration_hours"],
	)
	total = round(sum((r.get("duration_hours") or 0) for r in rows), 4)

	return {
		"week_total_hours": total,
		"week_start": str(monday),
		"work_days": get_work_days(),
	}


@frappe.whitelist()
def duplicate_entry(entry_name: str, target_date: str = None) -> dict:
	"""Duplicate an entry, optionally to a different date.

	When copying to a different date, start_time and end_time are NOT copied
	(a time slot on a different day is meaningless). Same-day copies keep them.
	"""
	src = frappe.get_doc("Watch Entry", entry_name)

	if src.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	effective_date = target_date or frappe.utils.today()
	same_day = str(effective_date) == str(src.date)

	new_entry = frappe.new_doc("Watch Entry")
	new_entry.date = effective_date
	new_entry.user = frappe.session.user
	new_entry.description = src.description
	new_entry.duration_hours = src.duration_hours
	new_entry.entry_type = src.entry_type
	new_entry.is_running = 0
	new_entry.contact = src.contact
	new_entry.context_type = src.context_type
	new_entry.context_name = src.context_name

	# Only copy time slots for same-day duplicates
	if same_day:
		new_entry.start_time = src.start_time
		new_entry.end_time = src.end_time
	else:
		new_entry.flags.keep_duration = True

	for tag_row in src.tags:
		new_entry.append("tags", {"tag": tag_row.tag})

	new_entry.insert(ignore_permissions=True)
	return _entry_to_dict(new_entry)


@frappe.whitelist()
def bulk_duplicate(entry_names: list, target_date: str = None) -> dict:
	"""Copy multiple entries to a target date. Skips running entries."""
	entry_names = _parse_json_list(entry_names)
	effective_date = target_date or frappe.utils.today()
	user = frappe.session.user
	created = []
	skipped = 0
	warnings: list[str] = []

	for ename in entry_names:
		src = frappe.get_doc("Watch Entry", ename)
		if src.user != user and not "System Manager" in frappe.get_roles():
			skipped += 1
			continue
		if src.is_running:
			skipped += 1
			warnings.append(_("{0} skipped — timer is running.").format(ename))
			continue

		same_day = str(effective_date) == str(src.date)
		new_entry = frappe.new_doc("Watch Entry")
		new_entry.date = effective_date
		new_entry.user = user
		new_entry.description = src.description
		new_entry.duration_hours = src.duration_hours
		new_entry.entry_type = src.entry_type
		new_entry.is_running = 0
		new_entry.contact = src.contact
		new_entry.context_type = src.context_type
		new_entry.context_name = src.context_name

		if same_day:
			new_entry.start_time = src.start_time
			new_entry.end_time = src.end_time
		else:
			new_entry.flags.keep_duration = True

		for tag_row in src.tags:
			new_entry.append("tags", {"tag": tag_row.tag})

		new_entry.insert(ignore_permissions=True)
		created.append(new_entry.name)

	return {"created": created, "skipped": skipped, "warnings": warnings}


@frappe.whitelist()
def check_yesterday_empty() -> dict:
	"""Return whether the previous configured work day had no entries.

	Used by the empty-yesterday nudge on the daily view.
	Returns { empty: bool, yesterday: str | null }
	  - yesterday: ISO date of the previous work day, or null if none applies
	"""
	from watch.api.settings import get_work_days
	work_days = get_work_days()  # list of ints: 0=Mon … 6=Sun

	if not work_days:
		return {"empty": False, "yesterday": None}

	# Walk backwards from today (exclusive) to find last configured work day
	today = date.today()
	candidate = today - timedelta(days=1)
	for _ in range(7):
		if candidate.weekday() in work_days:
			break
		candidate -= timedelta(days=1)
	else:
		return {"empty": False, "yesterday": None}

	count = frappe.db.count(
		"Watch Entry",
		{"user": frappe.session.user, "date": str(candidate), "is_running": 0},
	)
	return {"empty": count == 0, "yesterday": str(candidate)}


@frappe.whitelist()
def get_weekly_chart_data(week_start: str) -> dict:
	"""Return per-day and per-tag totals for the weekly visual charts.

	Uses the primary (highest-priority) tag per entry to avoid double-counting
	in the donut breakdown.
	"""
	user = frappe.session.user
	from datetime import date as date_type
	from watch.api.settings import get_work_days

	monday = date_type.fromisoformat(week_start)
	sunday = monday + timedelta(days=6)
	work_days = set(get_work_days())  # set of ints 0=Mon…6=Sun

	entries = frappe.get_all(
		"Watch Entry",
		filters={
			"user": user,
			"date": ["between", [str(monday), str(sunday)]],
			"is_running": 0,
		},
		fields=["name", "date", "duration_hours"],
	)
	entries = _attach_tags(entries)

	# ── Per-day totals ───────────────────────────────────────────────────
	day_labels = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
	daily = []
	for i in range(7):
		d = monday + timedelta(days=i)
		day_str = str(d)
		day_hours = round(
			sum(e.get("duration_hours") or 0 for e in entries if str(e["date"]) == day_str),
			4,
		)
		day_rounded = round(
			sum(round_hours(e.get("duration_hours") or 0) for e in entries if str(e["date"]) == day_str),
			4,
		)
		daily.append({
			"day": day_str,
			"label": day_labels[i],
			"hours": day_hours,
			"rounded_hours": day_rounded,
			"is_work_day": i in work_days,
		})

	total_hours = round(sum(d["hours"] for d in daily), 4)

	# ── Per-tag totals (primary tag only per entry to avoid double-counting) ─
	_PRIORITY = {"Client": 0, "Project": 1}

	tag_hours: dict = {}  # tag_name → {"color": str|None, "hours": float}
	untagged_hours = 0.0

	for e in entries:
		hours = e.get("duration_hours") or 0
		meta_list = e.get("tag_meta") or []
		if not meta_list:
			untagged_hours += hours
		else:
			primary = sorted(
				meta_list,
				key=lambda m: (_PRIORITY.get(m.get("category") or "", 2), m.get("tag_name", "")),
			)[0]
			tag_name = primary.get("tag_name") or primary.get("name", "")
			color = primary.get("color")
			if tag_name not in tag_hours:
				tag_hours[tag_name] = {"color": color, "hours": 0.0}
			tag_hours[tag_name]["hours"] = round(tag_hours[tag_name]["hours"] + hours, 4)

	tags = [
		{
			"tag_name": name,
			"color": meta["color"],
			"hours": round(meta["hours"], 4),
			"pct": round(meta["hours"] / total_hours * 100, 1) if total_hours else 0.0,
		}
		for name, meta in sorted(tag_hours.items(), key=lambda x: -x[1]["hours"])
	]
	if untagged_hours > 0:
		tags.append({
			"tag_name": None,
			"color": "#9ca3af",
			"hours": round(untagged_hours, 4),
			"pct": round(untagged_hours / total_hours * 100, 1) if total_hours else 0.0,
		})

	return {"daily": daily, "tags": tags, "total_hours": total_hours}


@frappe.whitelist()
def export_csv(
	from_date: str,
	to_date: str,
	tag: str = None,
	entry_type: str = None,
	entry_status: str = None,
) -> None:
	"""Stream a CSV of the current user's time entries. No state changes."""
	import csv
	import io

	user = frappe.session.user
	filters = {
		"user": user,
		"date": ["between", [from_date, to_date]],
		"is_running": 0,
	}
	if entry_type:
		filters["entry_type"] = entry_type
	if entry_status:
		filters["entry_status"] = entry_status

	entries = frappe.get_all(
		"Watch Entry",
		filters=filters,
		fields=[
			"name", "date", "start_time", "end_time",
			"duration_hours", "description", "entry_type",
			"entry_status", "contact", "context_type", "context_name",
		],
		order_by="date asc, start_time asc",
	)

	rows = []
	for entry in entries:
		tag_rows = frappe.get_all(
			"Watch Entry Tag",
			filters={"parent": entry.name},
			fields=["tag_name"],
			order_by="idx asc",
		)
		tag_names = [t.tag_name for t in tag_rows if t.tag_name]

		if tag and tag not in tag_names:
			continue

		entry["tags"] = ";".join(tag_names)
		rows.append(entry)

	output = io.StringIO()
	writer = csv.DictWriter(
		output,
		fieldnames=[
			"date", "start_time", "end_time",
			"duration_hours", "description", "tags",
			"entry_type", "entry_status",
			"contact", "context_type", "context_name",
		],
		extrasaction="ignore",
	)
	writer.writeheader()
	writer.writerows(rows)

	csv_bytes = "\ufeff" + output.getvalue()  # UTF-8 BOM for Excel
	filename = f"watch-export-{from_date}-{to_date}.csv"

	frappe.response["type"] = "download"
	frappe.response["doctype"] = filename
	frappe.response["result"] = csv_bytes
	frappe.response["content_type"] = "text/csv; charset=utf-8"


# ── Custom date range report (Feature #29) ────────────────────────────────


@frappe.whitelist()
def get_range_summary(from_date: str, to_date: str) -> dict:
	"""Return entries grouped by day for an arbitrary date range.

	Similar to get_weekly_summary but not limited to a single week.
	Includes rounded values and per-day/tag breakdowns.
	"""
	from datetime import date as date_type

	user = frappe.session.user
	start = date_type.fromisoformat(from_date)
	end = date_type.fromisoformat(to_date)

	entries = frappe.get_all(
		"Watch Entry",
		filters={
			"user": user,
			"date": ["between", [from_date, to_date]],
			"is_running": 0,
		},
		fields=[
			"name", "date", "start_time", "end_time", "duration_hours",
			"description", "entry_type", "entry_status", "is_running",
		],
		order_by="date asc, start_time asc",
	)
	entries = _attach_tags(entries)

	# Group by day
	days_map: dict[str, list] = {}
	current = start
	while current <= end:
		days_map[str(current)] = []
		current += timedelta(days=1)
	for e in entries:
		days_map.setdefault(str(e.date), []).append(e)

	from watch.api.settings import get_work_days
	work_days_set = set(get_work_days())

	days = []
	for day_str in sorted(days_map):
		day_entries = days_map[day_str]
		day_total = sum(e.get("duration_hours") or 0 for e in day_entries)
		day_billable = sum(
			(e.get("duration_hours") or 0)
			for e in day_entries
			if e.get("entry_type") == "billable"
		)
		day_rounded_total = sum(round_hours(e.get("duration_hours") or 0) for e in day_entries)
		day_rounded_billable = sum(
			round_hours(e.get("duration_hours") or 0)
			for e in day_entries
			if e.get("entry_type") == "billable"
		)
		d = date_type.fromisoformat(day_str)
		top, overflow = _top_tags(day_entries)
		days.append({
			"date": day_str,
			"total_hours": round(day_total, 4),
			"billable_hours": round(day_billable, 4),
			"rounded_total_hours": round(day_rounded_total, 4),
			"rounded_billable_hours": round(day_rounded_billable, 4),
			"entry_count": len(day_entries),
			"top_tags": top,
			"overflow_count": overflow,
			"is_work_day": d.weekday() in work_days_set,
		})

	total_hours = sum(d["total_hours"] for d in days)
	billable_hours = sum(d["billable_hours"] for d in days)
	rounded_total = sum(d["rounded_total_hours"] for d in days)
	rounded_billable = sum(d["rounded_billable_hours"] for d in days)

	# Per-tag breakdown (primary tag)
	_PRIORITY = {"Client": 0, "Project": 1}
	tag_hours: dict = {}
	untagged_hours = 0.0

	for e in entries:
		hours = e.get("duration_hours") or 0
		meta_list = e.get("tag_meta") or []
		if not meta_list:
			untagged_hours += hours
		else:
			primary = sorted(
				meta_list,
				key=lambda m: (_PRIORITY.get(m.get("category") or "", 2), m.get("tag_name", "")),
			)[0]
			tag_name = primary.get("tag_name") or primary.get("name", "")
			color = primary.get("color")
			if tag_name not in tag_hours:
				tag_hours[tag_name] = {"color": color, "hours": 0.0}
			tag_hours[tag_name]["hours"] = round(tag_hours[tag_name]["hours"] + hours, 4)

	tags = [
		{
			"tag_name": name,
			"color": meta["color"],
			"hours": round(meta["hours"], 4),
			"pct": round(meta["hours"] / total_hours * 100, 1) if total_hours else 0.0,
		}
		for name, meta in sorted(tag_hours.items(), key=lambda x: -x[1]["hours"])
	]
	if untagged_hours > 0:
		tags.append({
			"tag_name": None,
			"color": "#9ca3af",
			"hours": round(untagged_hours, 4),
			"pct": round(untagged_hours / total_hours * 100, 1) if total_hours else 0.0,
		})

	return {
		"from_date": from_date,
		"to_date": to_date,
		"days": days,
		"tags": tags,
		"total_hours": round(total_hours, 4),
		"billable_hours": round(billable_hours, 4),
		"rounded_total_hours": round(rounded_total, 4),
		"rounded_billable_hours": round(rounded_billable, 4),
	}


# ── Bulk operations (Feature #21) ─────────────────────────────────────────


@frappe.whitelist()
def bulk_add_tag(entry_names: list, tag: str) -> dict:
	"""Add a tag to multiple entries. Skips locked/sent entries and duplicates."""
	entry_names = _parse_json_list(entry_names)
	user = frappe.session.user
	updated = 0
	skipped = 0

	for ename in entry_names:
		entry = frappe.get_doc("Watch Entry", ename)
		if entry.user != user and not "System Manager" in frappe.get_roles():
			skipped += 1
			continue
		if entry.entry_status == "sent" or _is_soft_locked(str(entry.date)):
			skipped += 1
			continue

		# Skip if tag already present
		existing_tags = [t.tag for t in entry.tags]
		if tag in existing_tags:
			updated += 1  # not an error, just already there
			continue

		entry.append("tags", {"tag": tag})
		entry.save(ignore_permissions=True)
		updated += 1

	return {"updated": updated, "skipped": skipped}


@frappe.whitelist()
def bulk_set_entry_type(entry_names: list, entry_type: str) -> dict:
	"""Set entry_type on multiple entries. Skips locked/sent entries."""
	entry_names = _parse_json_list(entry_names)
	user = frappe.session.user
	updated = 0
	skipped = 0

	for ename in entry_names:
		entry = frappe.get_doc("Watch Entry", ename)
		if entry.user != user and not "System Manager" in frappe.get_roles():
			skipped += 1
			continue
		if entry.entry_status == "sent" or _is_soft_locked(str(entry.date)):
			skipped += 1
			continue

		entry.entry_type = entry_type
		entry.save(ignore_permissions=True)
		updated += 1

	return {"updated": updated, "skipped": skipped}


@frappe.whitelist()
def bulk_delete(entry_names: list) -> dict:
	"""Delete multiple entries. Skips sent and running entries."""
	entry_names = _parse_json_list(entry_names)
	user = frappe.session.user
	deleted = 0
	skipped = 0
	warnings: list[str] = []

	for ename in entry_names:
		entry = frappe.get_doc("Watch Entry", ename)
		if entry.user != user and not "System Manager" in frappe.get_roles():
			skipped += 1
			continue
		if entry.is_running:
			skipped += 1
			warnings.append(_("{0} skipped — timer is running.").format(ename))
			continue
		if entry.entry_status == "sent":
			skipped += 1
			warnings.append(_("{0} skipped — already sent.").format(ename))
			continue

		frappe.delete_doc("Watch Entry", ename, ignore_permissions=True)
		deleted += 1

	return {"deleted": deleted, "skipped": skipped, "warnings": warnings}
