# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Recurring Entry Templates API — favorites and day templates."""

import json

import frappe
from frappe import _


def _parse_json(val):
	"""Parse a JSON string if needed, otherwise return as-is."""
	if isinstance(val, str):
		return json.loads(val)
	return val


def _template_to_dict(template) -> dict:
	"""Return a template document as a serialisable dict with nested items+tags."""
	d = template.as_dict()
	# Group item_tags by item_idx for convenience
	tags_by_idx: dict[int, list] = {}
	for t in template.item_tags:
		tags_by_idx.setdefault(t.item_idx, []).append({
			"tag": t.tag,
			"tag_name": t.tag_name,
			"tag_color": t.tag_color,
			"tag_category": t.tag_category,
		})
	items = []
	for item in template.items:
		item_d = item.as_dict()
		item_d["tags"] = tags_by_idx.get(item.idx, [])
		items.append(item_d)
	d["items"] = items
	return d


@frappe.whitelist()
def get_favorites() -> list:
	"""Return sorted favorites for the current user's quick-add bar."""
	user = frappe.session.user
	templates = frappe.get_all(
		"Watch Entry Template",
		filters={"user": user, "template_type": "favorite"},
		fields=["name"],
		order_by="sort_order asc",
	)
	result = []
	for row in templates:
		tpl = frappe.get_doc("Watch Entry Template", row.name)
		result.append(_template_to_dict(tpl))
	return result


@frappe.whitelist()
def get_day_templates() -> list:
	"""Return all day templates for the current user."""
	user = frappe.session.user
	templates = frappe.get_all(
		"Watch Entry Template",
		filters={"user": user, "template_type": "day"},
		fields=["name"],
		order_by="template_name asc",
	)
	result = []
	for row in templates:
		tpl = frappe.get_doc("Watch Entry Template", row.name)
		d = _template_to_dict(tpl)
		# Add summary stats for the picker UI
		total_hours = sum((i.get("duration_hours") or 0) for i in d["items"])
		d["entry_count"] = len(d["items"])
		d["total_hours"] = round(total_hours, 4)
		result.append(d)
	return result


@frappe.whitelist()
def save_from_entry(
	entry_name: str,
	template_name: str,
	slot: int,
	keep_duration: bool = False,
) -> dict:
	"""Create a favorite from an existing Watch Entry."""
	slot = int(slot)
	keep_duration = bool(int(keep_duration)) if isinstance(keep_duration, str) else bool(keep_duration)

	entry = frappe.get_doc("Watch Entry", entry_name)
	if entry.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	tpl = frappe.new_doc("Watch Entry Template")
	tpl.template_name = template_name
	tpl.template_type = "favorite"
	tpl.user = frappe.session.user
	tpl.sort_order = slot

	tpl.append("items", {
		"description": entry.description,
		"billing_type": entry.entry_type or "billable",
		"duration_hours": entry.duration_hours if keep_duration else 0,
	})

	# Copy tags from the entry
	for tag_row in entry.tags:
		tpl.append("item_tags", {
			"item_idx": 1,
			"tag": tag_row.tag,
		})

	tpl.insert(ignore_permissions=True)
	return _template_to_dict(tpl)


@frappe.whitelist()
def save_day_template(
	date: str,
	template_name: str,
	entry_names: list = None,
) -> dict:
	"""Create a day template from selected entries on a given date."""
	entry_names = _parse_json(entry_names) if entry_names else []

	if not entry_names:
		frappe.throw(_("Select at least one entry to include in the template."))

	tpl = frappe.new_doc("Watch Entry Template")
	tpl.template_name = template_name
	tpl.template_type = "day"
	tpl.user = frappe.session.user
	tpl.sort_order = 0

	for idx, ename in enumerate(entry_names, start=1):
		entry = frappe.get_doc("Watch Entry", ename)
		if entry.user != frappe.session.user and not "System Manager" in frappe.get_roles():
			frappe.throw(_("Not permitted"), frappe.PermissionError)

		tpl.append("items", {
			"description": entry.description,
			"billing_type": entry.entry_type or "billable",
			"duration_hours": entry.duration_hours or 0,
		})

		for tag_row in entry.tags:
			tpl.append("item_tags", {
				"item_idx": idx,
				"tag": tag_row.tag,
			})

	tpl.insert(ignore_permissions=True)
	return _template_to_dict(tpl)


@frappe.whitelist()
def apply_day_template(template_name: str, date: str) -> dict:
	"""Create time entries from a day template for the given date.

	Returns the list of created entry dicts.
	"""
	tpl = frappe.get_doc("Watch Entry Template", template_name)
	if tpl.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if tpl.template_type != "day":
		frappe.throw(_("Only day templates can be applied."))

	# Group tags by item_idx
	tags_by_idx: dict[int, list] = {}
	for t in tpl.item_tags:
		tags_by_idx.setdefault(t.item_idx, []).append(t.tag)

	created = []
	for item in tpl.items:
		entry = frappe.new_doc("Watch Entry")
		entry.date = date
		entry.user = frappe.session.user
		entry.description = item.description
		entry.entry_type = item.billing_type or "billable"
		entry.duration_hours = item.duration_hours or 0
		entry.entry_status = "draft"
		entry.is_running = 0

		for tag_name in tags_by_idx.get(item.idx, []):
			entry.append("tags", {"tag": tag_name})

		entry.insert(ignore_permissions=True)
		created.append(entry.as_dict())

	return {"entries": created, "count": len(created)}


@frappe.whitelist()
def delete_template(template_name: str) -> dict:
	"""Delete a favorite or day template."""
	tpl = frappe.get_doc("Watch Entry Template", template_name)
	if tpl.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	frappe.delete_doc("Watch Entry Template", template_name, ignore_permissions=True)
	return {"deleted": template_name}


@frappe.whitelist()
def update_template(
	template_name: str,
	new_name: str = None,
	slot: int = None,
	items: list = None,
) -> dict:
	"""Update a template's name, slot, or items."""
	tpl = frappe.get_doc("Watch Entry Template", template_name)
	if tpl.user != frappe.session.user and not "System Manager" in frappe.get_roles():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if new_name is not None:
		tpl.template_name = new_name
	if slot is not None:
		tpl.sort_order = int(slot)

	if items is not None:
		items = _parse_json(items)
		tpl.set("items", [])
		tpl.set("item_tags", [])
		for idx, item_data in enumerate(items, start=1):
			tpl.append("items", {
				"description": item_data.get("description"),
				"billing_type": item_data.get("billing_type", "billable"),
				"duration_hours": item_data.get("duration_hours", 0),
			})
			for tag in (item_data.get("tags") or []):
				tag_name = tag if isinstance(tag, str) else tag.get("tag", tag.get("name"))
				tpl.append("item_tags", {
					"item_idx": idx,
					"tag": tag_name,
				})

	tpl.save(ignore_permissions=True)
	return _template_to_dict(tpl)


@frappe.whitelist()
def reorder_favorites(order: list) -> dict:
	"""Reorder favorites by reassigning slot numbers.

	Args:
		order: list of template names in desired order (slot 1, 2, 3...)
	"""
	order = _parse_json(order)
	user = frappe.session.user

	# Validate all templates before reassigning
	templates = []
	for tpl_name in order:
		tpl = frappe.get_doc("Watch Entry Template", tpl_name)
		if tpl.user != user:
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		if tpl.template_type != "favorite":
			frappe.throw(_("Can only reorder favorites."))
		templates.append(tpl)

	# Clear all slots first (use DB directly to bypass validation)
	for tpl in templates:
		frappe.db.set_value("Watch Entry Template", tpl.name, "sort_order", 0)

	# Reassign in order
	for slot, tpl in enumerate(templates, start=1):
		tpl.reload()
		tpl.sort_order = slot
		tpl.save(ignore_permissions=True)

	return {"reordered": len(order)}
