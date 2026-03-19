# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


# ── Helpers ───────────────────────────────────────────────────────────────────

def _attach_tag_meta(entries: list) -> None:
	"""Attach tag_names, client_tag, client_tag_color, and project_tag to each entry in-place."""
	if not entries:
		return
	entry_names = [e.name for e in entries]
	tag_rows = frappe.get_all(
		"Watch Entry Tag",
		filters={"parent": ["in", entry_names]},
		fields=["parent", "tag", "tag_name", "tag_color", "tag_category"],
		order_by="idx asc",
	)
	tags_map: dict[str, list] = {}
	for row in tag_rows:
		tags_map.setdefault(row.parent, []).append(row)

	for e in entries:
		rows = tags_map.get(e.name, [])
		e["tag_names"] = [r.tag_name or r.tag for r in rows]

		# Client-category tag (first one found)
		client_row = next((r for r in rows if r.tag_category == "Client"), None)
		e["client_tag"]       = client_row.tag_name if client_row else None
		e["client_tag_color"] = client_row.tag_color if client_row else None

		# Project-category tag (first one found)
		project_row = next((r for r in rows if r.tag_category == "Project"), None)
		e["project_tag"] = project_row.tag_name if project_row else None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_draft_billable(
	user: str,
	client_tag: str | None,
	from_date: str,
	to_date: str,
) -> list:
	"""
	Return all draft billable entries for the date range, filtered by client.

	client_tag semantics:
	  None  — no filter: return all draft billable entries
	  ""    — return only entries with no Client-category tag (unassigned)
	  "Acme Corp" — return only entries whose Client tag matches
	"""
	entries = frappe.get_all(
		"Watch Entry",
		filters={
			"user":         user,
			"date":         ["between", [from_date, to_date]],
			"entry_type":   "billable",
			"entry_status": "draft",
			"is_running":   0,
		},
		fields=[
			"name", "date", "description",
			"duration_hours", "entry_type",
		],
		order_by="date asc",
	)
	_attach_tag_meta(entries)

	if client_tag is None:
		return entries                                              # all
	if not client_tag:                                             # ""
		return [e for e in entries if e["client_tag"] is None]    # unassigned
	return [e for e in entries if e["client_tag"] == client_tag]  # specific


def _mark_entries_sent(entry_names: list[str]) -> None:
	for name in entry_names:
		frappe.db.set_value("Watch Entry", name, "entry_status", "sent")
	frappe.db.commit()


# ── API ───────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_summary(from_date: str, to_date: str) -> dict:
	"""
	Return billable entries grouped by Client tag, sub-grouped by Project tag,
	plus non-billable and internal totals.
	"""
	user = frappe.session.user

	all_entries = frappe.get_all(
		"Watch Entry",
		filters={"user": user, "date": ["between", [from_date, to_date]], "is_running": 0},
		fields=[
			"name", "date", "duration_hours",
			"description", "entry_type", "entry_status",
		],
		order_by="date asc",
	)
	_attach_tag_meta(all_entries)

	# Split by entry_type
	billable  = [e for e in all_entries if e.entry_type == "billable"]
	internal  = [e for e in all_entries if e.entry_type == "internal"]
	non_bill  = [e for e in all_entries if e.entry_type == "non-billable"]

	# Group billable entries by client tag
	groups_map: dict[str, dict] = {}   # client_tag → group
	for e in billable:
		key = e["client_tag"] or "__unassigned__"
		if key not in groups_map:
			groups_map[key] = {
				"client_tag":       e["client_tag"],
				"client_tag_color": e["client_tag_color"],
				"total_hours":      0.0,
				"entry_status":     "draft",
				"projects":         {},
			}
		g = groups_map[key]
		g["total_hours"] = round(g["total_hours"] + (e.duration_hours or 0), 4)
		if e.entry_status == "sent":
			g["entry_status"] = "sent"

		# Sub-group by project tag
		proj_key = e["project_tag"]  # None → untagged project
		if proj_key not in g["projects"]:
			g["projects"][proj_key] = {
				"project_tag":   proj_key,
				"hours":         0.0,
				"entries":       [],
			}
		p = g["projects"][proj_key]
		p["hours"] = round(p["hours"] + (e.duration_hours or 0), 4)
		p["entries"].append({
			"name":           e.name,
			"date":           str(e.date),
			"description":    e.description or "",
			"duration_hours": e.duration_hours or 0,
			"entry_status":   e.entry_status,
		})

	# Flatten and sort: named clients first (alphabetical), then Unassigned
	groups = []
	for key in sorted(groups_map):
		g = groups_map[key]
		g["projects"] = list(g["projects"].values())
		groups.append(g)

	# Move __unassigned__ to the end
	groups.sort(key=lambda g: (g["client_tag"] is None, g["client_tag"] or ""))

	totals = {
		"billable_hours":     round(sum(e.duration_hours or 0 for e in billable), 4),
		"non_billable_hours": round(sum(e.duration_hours or 0 for e in non_bill), 4),
		"internal_hours":     round(sum(e.duration_hours or 0 for e in internal), 4),
	}

	return {
		"from_date": from_date,
		"to_date":   to_date,
		"groups":    groups,
		"totals":    totals,
	}


@frappe.whitelist()
def mark_sent(from_date: str, to_date: str, client_tag: str = None) -> dict:
	"""
	Mark all draft billable entries in the date range (optionally filtered to
	a specific client tag) as sent.  Returns the count of updated entries.
	"""
	user = frappe.session.user
	filters = {
		"user":         user,
		"date":         ["between", [from_date, to_date]],
		"entry_type":   "billable",
		"entry_status": "draft",
		"is_running":   0,
	}
	entries = frappe.get_all("Watch Entry", filters=filters, fields=["name"])

	if client_tag is not None:
		# Filter to entries whose client tag matches
		if entries:
			entry_names = [e.name for e in entries]
			tag_rows = frappe.get_all(
				"Watch Entry Tag",
				filters={"parent": ["in", entry_names], "tag_category": "Client"},
				fields=["parent", "tag_name"],
				order_by="idx asc",
			)
			# First client tag per entry
			client_map: dict[str, str] = {}
			for row in tag_rows:
				if row.parent not in client_map:
					client_map[row.parent] = row.tag_name

			entries = [
				e for e in entries
				if (client_map.get(e.name) == client_tag)
				or (client_tag == "" and e.name not in client_map)
			]

	count = 0
	for e in entries:
		frappe.db.set_value("Watch Entry", e.name, "entry_status", "sent")
		count += 1

	frappe.db.commit()
	return {"updated": count}


@frappe.whitelist()
def get_billing_actions() -> list:
	"""Discover installed apps that have registered watch_billing_actions."""
	all_actions = frappe.get_hooks("watch_billing_actions")
	if not all_actions:
		return []

	installed_apps = frappe.get_installed_apps()
	result = []
	for action in all_actions:
		if isinstance(action, dict) and action.get("app") in installed_apps:
			result.append(action)
	return result


@frappe.whitelist()
def forward_to_app(
	action_endpoint: str,
	client_tag: str = None,
	from_date: str = None,
	to_date: str = None,
) -> dict:
	"""
	Call a registered invoicing app's endpoint with the billable entry payload,
	then mark all forwarded entries as sent.  Returns forwarded totals and
	an optional draft_url if the invoicing app provides one.
	"""
	# Security: only allow endpoints from registered, installed actions
	all_actions = frappe.get_hooks("watch_billing_actions")
	installed_apps = frappe.get_installed_apps()
	valid_endpoints = {
		a["endpoint"]
		for a in (all_actions or [])
		if isinstance(a, dict) and a.get("app") in installed_apps
	}
	if action_endpoint not in valid_endpoints:
		frappe.throw(_("Action endpoint '{0}' is not registered").format(action_endpoint))

	user = frappe.session.user
	# client_tag: None = all clients, "" = unassigned, non-empty = specific client
	entries = _collect_draft_billable(user, client_tag, from_date, to_date)

	if not entries:
		frappe.throw(_("No billable draft entries found for this client and date range"))

	total_hours = round(sum(e.duration_hours or 0 for e in entries), 4)

	payload = {
		"client_tag":   client_tag,
		"from_date":    from_date,
		"to_date":      to_date,
		"total_hours":  total_hours,
		"entries": [
			{
				"name":           e.name,
				"date":           str(e.date),
				"description":    e.description or "",
				"duration_hours": e.duration_hours or 0,
				"entry_type":     e.entry_type,
				"tags":           e["tag_names"],
			}
			for e in entries
		],
	}

	# Call the registered endpoint (invoicing app is on the same instance)
	try:
		endpoint_fn = frappe.get_attr(action_endpoint)
		result = endpoint_fn(**payload) or {}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "watch.api.billing.forward_to_app")
		frappe.throw(_("Forward failed — see error log for details"))

	_mark_entries_sent([e.name for e in entries])

	return {
		"forwarded_hours": total_hours,
		"forwarded_count": len(entries),
		"draft_url":       result.get("draft_url") if isinstance(result, dict) else None,
	}


@frappe.whitelist()
def export_csv(
	client_tag: str = None,
	from_date: str = None,
	to_date: str = None,
) -> dict:
	"""
	Generate a CSV of draft billable entries for a client/date range,
	mark them as sent, and return the CSV content as a string.
	"""
	import csv
	import io

	user = frappe.session.user
	# client_tag: None = all clients, "" = unassigned, non-empty = specific client
	entries = _collect_draft_billable(user, client_tag, from_date, to_date)

	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow(["date", "description", "duration_hours", "tags", "entry_type"])
	for e in entries:
		writer.writerow([
			str(e.date),
			e.description or "",
			e.duration_hours or 0,
			"; ".join(e["tag_names"]),
			e.entry_type or "",
		])

	_mark_entries_sent([e.name for e in entries])

	if client_tag is None:
		slug = "all"
	else:
		slug = (client_tag or "unassigned").lower().replace(" ", "-")
	return {
		"csv":            buf.getvalue(),
		"filename":       f"watch-{slug}-{from_date}-{to_date}.csv",
		"exported_count": len(entries),
	}
