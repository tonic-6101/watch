# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _

from watch.utils.contexts import get_context_display_value, get_timer_context_options


# ── Context helpers ──────────────────────────────────────────────────────────

def _build_context_label_map() -> dict[str, str]:
	"""Return {doctype: label} for all registered timer context types."""
	return {ctx["doctype"]: ctx["label"] for ctx in get_timer_context_options()}


def _resolve_contact_display(contact: str | None) -> str | None:
	"""Return full_name (or contact_name) for a Contact link, or None."""
	if not contact:
		return None
	try:
		# Frappe Contact stores the display name in 'full_name' (computed) or
		# fallback to 'first_name'.
		val = frappe.db.get_value("Contact", contact, "full_name")
		return val or contact
	except Exception:
		return contact


# ── Tag helpers ──────────────────────────────────────────────────────────────

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


# ── Collection helper ────────────────────────────────────────────────────────

def _collect_draft_billable(
	user: str,
	client_tag: str | None,
	from_date: str,
	to_date: str,
	contact: str | None = None,
	context_name: str | None = None,
) -> list:
	"""
	Return all draft billable entries for the date range, with optional filters.

	client_tag semantics:
	  None  — no filter: return all draft billable entries
	  ""    — return only entries with no Client-category tag (unassigned)
	  "Acme Corp" — return only entries whose Client tag matches

	contact — if provided, filter to entries linked to this Contact record.
	context_name — if provided, filter to entries whose context_name matches.
	"""
	filters = {
		"user":         user,
		"date":         ["between", [from_date, to_date]],
		"entry_type":   "billable",
		"entry_status": "draft",
		"is_running":   0,
	}
	if contact is not None and contact != "":
		filters["contact"] = contact
	if context_name is not None and context_name != "":
		filters["context_name"] = context_name

	entries = frappe.get_all(
		"Watch Entry",
		filters=filters,
		fields=[
			"name", "date", "description",
			"duration_hours", "entry_type",
			"contact", "context_type", "context_name",
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


# ── API ──────────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_summary(
	from_date: str,
	to_date: str,
	contact: str | None = None,
	context_name: str | None = None,
) -> dict:
	"""
	Return billable entries grouped by Contact/Client (level 1),
	Project context or tag (level 2), Task context (level 3),
	plus non-billable and internal totals.

	Level 1: contact field → fall back to Client tag when empty
	Level 2: context_name where registered label = "Project" → fall back to Project tag
	Level 3: context_name where registered label = "Task"
	Event context (label = "Event") or other labels → entry detail, not grouped
	"""
	user = frappe.session.user

	# Build context label map: {doctype: label}
	ctx_label_map = _build_context_label_map()

	base_filters: dict = {
		"user": user,
		"date": ["between", [from_date, to_date]],
		"is_running": 0,
	}
	if contact is not None and contact != "":
		base_filters["contact"] = contact
	if context_name is not None and context_name != "":
		base_filters["context_name"] = context_name

	all_entries = frappe.get_all(
		"Watch Entry",
		filters=base_filters,
		fields=[
			"name", "date", "duration_hours",
			"description", "entry_type", "entry_status",
			"contact", "context_type", "context_name",
		],
		order_by="date asc",
	)
	_attach_tag_meta(all_entries)

	# Split by entry_type
	billable  = [e for e in all_entries if e.entry_type == "billable"]
	internal  = [e for e in all_entries if e.entry_type == "internal"]
	non_bill  = [e for e in all_entries if e.entry_type == "non-billable"]

	# ── Collect available filter values (distinct, from ALL entries in range) ──
	contacts_set: dict[str, str] = {}   # name → display
	projects_set: dict[str, str] = {}   # context_name → display

	for e in all_entries:
		# Contacts
		if e.get("contact"):
			if e.contact not in contacts_set:
				contacts_set[e.contact] = _resolve_contact_display(e.contact) or e.contact

		# Projects (context with label = "Project")
		if e.get("context_type") and e.get("context_name"):
			label = ctx_label_map.get(e.context_type)
			if label == "Project" and e.context_name not in projects_set:
				display = get_context_display_value(e.context_type, e.context_name)
				projects_set[e.context_name] = display or e.context_name

	available_contacts = [
		{"name": k, "display": v}
		for k, v in sorted(contacts_set.items(), key=lambda x: x[1])
	]
	available_projects = [
		{"name": k, "display": v}
		for k, v in sorted(projects_set.items(), key=lambda x: x[1])
	]

	# ── Classify each entry's contexts by label ──
	def _classify_entry_contexts(entry):
		"""Return (project_ctx_name, project_display, task_ctx_name, task_display,
		           event_ctx_name, event_display) based on context_type label."""
		project_ctx = None
		project_display = None
		task_ctx = None
		task_display = None
		event_ctx = None
		event_display = None

		ct = entry.get("context_type")
		cn = entry.get("context_name")
		if ct and cn:
			label = ctx_label_map.get(ct)
			display = get_context_display_value(ct, cn) or cn
			if label == "Project":
				project_ctx = cn
				project_display = display
			elif label == "Task":
				task_ctx = cn
				task_display = display
			elif label == "Event":
				event_ctx = cn
				event_display = display
			# Other labels are treated like events (detail, not grouped)
			elif label:
				event_ctx = cn
				event_display = display

		return project_ctx, project_display, task_ctx, task_display, event_ctx, event_display

	# ── Group billable entries: Level 1 → Level 2 → Level 3 ──
	groups_map: dict[str, dict] = {}   # group_key → group

	for e in billable:
		(
			proj_ctx, proj_display,
			task_ctx, task_display,
			event_ctx, event_display,
		) = _classify_entry_contexts(e)

		# Level 1 key: contact or client_tag
		entry_contact = e.get("contact")
		if entry_contact:
			l1_key = f"contact:{entry_contact}"
			is_tag_based_l1 = False
			contact_val = entry_contact
			contact_name_val = _resolve_contact_display(entry_contact) or entry_contact
			client_tag_val = e["client_tag"]
			client_tag_color_val = e["client_tag_color"]
		else:
			tag = e["client_tag"] or "__unassigned__"
			l1_key = f"tag:{tag}"
			is_tag_based_l1 = True
			contact_val = None
			contact_name_val = e["client_tag"]  # None for unassigned
			client_tag_val = e["client_tag"]
			client_tag_color_val = e["client_tag_color"]

		if l1_key not in groups_map:
			groups_map[l1_key] = {
				"contact":          contact_val,
				"contact_name":     contact_name_val,
				"client_tag":       client_tag_val,
				"client_tag_color": client_tag_color_val,
				"is_tag_based":     is_tag_based_l1,
				"total_hours":      0.0,
				"entry_status":     "draft",
				"_projects_map":    {},
			}
		g = groups_map[l1_key]
		g["total_hours"] = round(g["total_hours"] + (e.duration_hours or 0), 4)
		if e.entry_status == "sent":
			g["entry_status"] = "sent"

		# Level 2 key: project context or project tag
		if proj_ctx:
			l2_key = f"ctx:{proj_ctx}"
			is_tag_based_l2 = False
			l2_ctx_name = proj_ctx
			l2_display = proj_display
			l2_tag = e["project_tag"]
		else:
			ptag = e["project_tag"]
			l2_key = f"tag:{ptag}" if ptag else "__no_project__"
			is_tag_based_l2 = True if ptag else True
			l2_ctx_name = None
			l2_display = ptag  # None for untagged
			l2_tag = ptag

		if l2_key not in g["_projects_map"]:
			g["_projects_map"][l2_key] = {
				"context_name":    l2_ctx_name,
				"project_display": l2_display,
				"project_tag":     l2_tag,
				"is_tag_based":    is_tag_based_l2,
				"hours":           0.0,
				"_tasks_map":      {},
			}
		p = g["_projects_map"][l2_key]
		p["hours"] = round(p["hours"] + (e.duration_hours or 0), 4)

		# Level 3 key: task context (no tag fallback for tasks)
		if task_ctx:
			l3_key = f"ctx:{task_ctx}"
		else:
			l3_key = "__no_task__"

		if l3_key not in p["_tasks_map"]:
			p["_tasks_map"][l3_key] = {
				"context_name":  task_ctx,
				"task_display":  task_display,
				"hours":         0.0,
				"entries":       [],
			}
		t = p["_tasks_map"][l3_key]
		t["hours"] = round(t["hours"] + (e.duration_hours or 0), 4)

		entry_dict = {
			"name":           e.name,
			"date":           str(e.date),
			"description":    e.description or "",
			"duration_hours": e.duration_hours or 0,
			"entry_status":   e.entry_status,
			"contact":        e.get("contact"),
			"context_type":   e.get("context_type"),
			"context_name":   e.get("context_name"),
		}
		# Attach event context as detail info if present
		if event_ctx:
			entry_dict["event_context_name"] = event_ctx
			entry_dict["event_display"] = event_display

		t["entries"].append(entry_dict)

	# ── Flatten nested maps into sorted lists ──
	groups = []
	for g in groups_map.values():
		projects = []
		for p in g["_projects_map"].values():
			tasks = list(p["_tasks_map"].values())
			# Sort tasks: named tasks first, then no-task
			tasks.sort(key=lambda t: (t["context_name"] is None, t["task_display"] or ""))
			p["tasks"] = tasks
			del p["_tasks_map"]
			projects.append(p)
		# Sort projects: named first, then untagged/no-project
		projects.sort(key=lambda p: (
			p["project_display"] is None,
			p["project_display"] or "",
		))
		g["projects"] = projects
		del g["_projects_map"]
		groups.append(g)

	# Sort groups: contact-based first (alphabetical), then tag-based, then unassigned
	groups.sort(key=lambda g: (
		g["is_tag_based"],
		g["contact_name"] is None,
		(g["contact_name"] or "").lower(),
	))

	totals = {
		"billable_hours":     round(sum(e.duration_hours or 0 for e in billable), 4),
		"non_billable_hours": round(sum(e.duration_hours or 0 for e in non_bill), 4),
		"internal_hours":     round(sum(e.duration_hours or 0 for e in internal), 4),
	}

	return {
		"from_date":           from_date,
		"to_date":             to_date,
		"groups":              groups,
		"totals":              totals,
		"available_contacts":  available_contacts,
		"available_projects":  available_projects,
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
	contact: str | None = None,
	context_name: str | None = None,
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
	entries = _collect_draft_billable(
		user, client_tag, from_date, to_date,
		contact=contact, context_name=context_name,
	)

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
				"contact":        e.get("contact"),
				"context_type":   e.get("context_type"),
				"context_name":   e.get("context_name"),
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
	contact: str | None = None,
	context_name: str | None = None,
) -> dict:
	"""
	Generate a CSV of draft billable entries for a client/date range,
	mark them as sent, and return the CSV content as a string.
	"""
	import csv
	import io

	user = frappe.session.user
	# client_tag: None = all clients, "" = unassigned, non-empty = specific client
	entries = _collect_draft_billable(
		user, client_tag, from_date, to_date,
		contact=contact, context_name=context_name,
	)

	buf = io.StringIO()
	writer = csv.writer(buf)
	writer.writerow([
		"date", "description", "duration_hours", "tags", "entry_type",
		"contact", "context_type", "context_name",
	])
	for e in entries:
		writer.writerow([
			str(e.date),
			e.description or "",
			e.duration_hours or 0,
			"; ".join(e["tag_names"]),
			e.entry_type or "",
			e.get("contact") or "",
			e.get("context_type") or "",
			e.get("context_name") or "",
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
