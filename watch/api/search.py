# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


def _fmt_hours(h: float) -> str:
	"""1.5 → '1:30h', 0.75 → '0:45h'"""
	total_min = round((h or 0) * 60)
	return f"{total_min // 60}:{total_min % 60:02d}h"


def _fmt_date(d) -> str:
	"""date/str → '9 Mar'"""
	from datetime import date as date_type
	if not isinstance(d, date_type):
		d = date_type.fromisoformat(str(d))
	return f"{d.day} {d.strftime('%b')}"


# ── Section 1: Time Entries ───────────────────────────────────────────────────

@frappe.whitelist()
def search_entries(query: str) -> list:
	if not query or len(query) < 2:
		return []

	rows = frappe.db.sql("""
		SELECT
			e.name,
			e.description,
			e.date,
			e.duration_hours,
			e.contact,
			e.context_type,
			e.context_name,
			GROUP_CONCAT(t.tag_name ORDER BY et.idx SEPARATOR ', ') AS tags
		FROM `tabWatch Entry` e
		LEFT JOIN `tabWatch Entry Tag` et ON et.parent = e.name
		LEFT JOIN `tabWatch Tag` t ON t.name = et.tag
		WHERE e.user = %(user)s
		  AND e.date >= %(cutoff)s
		  AND e.description LIKE %(q)s
		GROUP BY e.name
		ORDER BY e.date DESC
		LIMIT 8
	""", {
		"user": frappe.session.user,
		"cutoff": frappe.utils.add_days(frappe.utils.today(), -90),
		"q": f"%{query}%",
	}, as_dict=True)

	results = []
	for row in rows:
		dur = _fmt_hours(row.duration_hours)
		date_str = _fmt_date(row.date)
		description_line = f"{dur} · {date_str}"
		if row.tags:
			first_tag = row.tags.split(", ")[0]
			description_line += f" · {first_tag}"
		# Add context info when available
		context_parts = []
		if row.contact:
			contact_name = frappe.db.get_value("Contact", row.contact, "full_name")
			if contact_name:
				context_parts.append(contact_name)
		if row.context_name and row.context_type:
			from watch.utils.contexts import get_context_display_value
			display = get_context_display_value(row.context_type, row.context_name)
			if display:
				context_parts.append(display)
		if context_parts:
			description_line += f" · {' · '.join(context_parts)}"
		results.append({
			"label": row.description or _("(no description)"),
			"description": description_line,
			"route": f"/watch/{row.date}",
			"icon": "clock",
			"meta": "entry",
		})
	return results


# ── Section 2: Tags ───────────────────────────────────────────────────────────

@frappe.whitelist()
def search_tags(query: str) -> list:
	if not query or len(query) < 1:
		return []

	tags = frappe.get_all(
		"Watch Tag",
		filters={"tag_name": ["like", f"%{query}%"]},
		fields=["name", "tag_name", "category"],
		limit=6,
		order_by="tag_name asc",
	)
	if not tags:
		return []

	# Count entries this month per tag (batch query)
	from datetime import date
	today = date.today()
	month_start = today.replace(day=1).isoformat()

	tag_names = [t.name for t in tags]
	placeholders = ", ".join(["%s"] * len(tag_names))
	counts_raw = frappe.db.sql(f"""
		SELECT et.tag, COUNT(DISTINCT e.name) AS cnt
		FROM `tabWatch Entry Tag` et
		JOIN `tabWatch Entry` e ON e.name = et.parent
		WHERE et.tag IN ({placeholders})
		  AND e.date >= %s
		GROUP BY et.tag
	""", tag_names + [month_start], as_dict=True)
	counts = {r.tag: r.cnt for r in counts_raw}

	results = []
	for tag in tags:
		cnt = counts.get(tag.name, 0)
		category = tag.category or _("Tag")
		description_line = f"{category} · {cnt} {_('entries this month')}"

		if tag.category == "Client":
			import urllib.parse
			route = f"/watch/prepare?client={urllib.parse.quote(tag.tag_name)}"
		else:
			route = "/watch/tags"

		results.append({
			"label": tag.tag_name,
			"description": description_line,
			"route": route,
			"icon": "tag",
			"meta": "tag",
		})
	return results


# ── Section 3: Start Timer ────────────────────────────────────────────────────

@frappe.whitelist()
def timer_action(query: str) -> list:
	if not query:
		return []

	user = frappe.session.user
	timer = None
	if frappe.db.exists("Watch Timer", user):
		timer = frappe.get_doc("Watch Timer", user)

	is_running = timer and timer.state in ("running", "paused")

	# Hint line: last used tag + entry type
	hint_parts = []
	last_entry = frappe.get_all(
		"Watch Entry",
		filters={"user": user, "is_running": 0},
		fields=["name", "entry_type"],
		order_by="creation desc",
		limit=1,
	)
	if last_entry:
		hint_parts.append(last_entry[0].entry_type or "billable")
		tag_row = frappe.get_all(
			"Watch Entry Tag",
			filters={"parent": last_entry[0].name},
			fields=["tag_name"],
			limit=1,
		)
		if tag_row and tag_row[0].tag_name:
			hint_parts.append(tag_row[0].tag_name)
	hint = " · ".join(hint_parts) if hint_parts else _("Billable")

	if is_running:
		label = _('Stop current & start: "{0}"').format(query)
	else:
		label = _('Start timer: "{0}"').format(query)

	return [{
		"label": label,
		"description": hint,
		"icon": "play",
		"action": "watch.api.timer.start_timer",
		"action_args": {"description": query},
		"meta": "action",
	}]


# ── Section 4: Navigation Shortcuts ──────────────────────────────────────────

@frappe.whitelist()
def navigation_shortcuts(query: str) -> list:
	if not query:
		return []

	from datetime import date, timedelta

	today = date.today()
	# Monday of current week
	monday = today - timedelta(days=today.weekday())
	week_label = monday.strftime("Week %-W")

	# Static nav table: (keywords, label, description, route, icon)
	nav_items = [
		(
			["today", "entries", "time"],
			_("Today"),
			_("Daily view"),
			"/watch",
			"calendar-days",
		),
		(
			["week", "weekly"],
			_("Week"),
			f"{week_label}",
			f"/watch/week/{monday.isoformat()}",
			"calendar-range",
		),
		(
			["prepare", "summary", "forward"],
			_("Prepare"),
			f"{week_label}",
			"/watch/prepare",
			"file-text",
		),
		(
			["range", "report", "date", "custom"],
			_("Range"),
			_("Date range report"),
			"/watch/range",
			"calendar-search",
		),
		(
			["settings"],
			_("Settings"),
			_("Watch Settings"),
			"/watch/settings",
			"settings",
		),
		(
			["tags", "clients"],
			_("Tags"),
			_("Tag management"),
			"/watch/tags",
			"tag",
		),
	]

	q = query.lower().strip()
	matches = []
	for keywords, label, description, route, icon in nav_items:
		if any(kw.startswith(q) or q in kw for kw in keywords):
			matches.append({
				"label": label,
				"description": description,
				"route": route,
				"icon": icon,
				"meta": "nav",
			})
		if len(matches) == 3:
			break

	return matches
