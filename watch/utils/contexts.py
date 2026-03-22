# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe


def get_timer_context_options() -> list[dict]:
	"""Collect context types from all installed apps via watch_timer_contexts hook.

	Returns list of dicts:
	    [
	        {
	            "doctype": "Orga Project",
	            "label": "Project",
	            "search_fields": ["project_name"],
	            "display_field": "project_name",
	            "parent_field": None,
	            "parent_doctype": None,
	        },
	        ...
	    ]
	"""
	contexts = []
	seen = set()
	for app in frappe.get_installed_apps():
		app_contexts = frappe.get_hooks("watch_timer_contexts", app_name=app)
		for ctx in app_contexts:
			if isinstance(ctx, dict) and ctx.get("doctype") not in seen:
				seen.add(ctx["doctype"])
				contexts.append({
					"doctype": ctx["doctype"],
					"label": ctx.get("label", ctx["doctype"]),
					"search_fields": ctx.get("search_fields", ["name"]),
					"display_field": ctx.get("display_field", "name"),
					"parent_field": ctx.get("parent_field"),
					"parent_doctype": ctx.get("parent_doctype"),
				})
	return contexts


def get_context_type_options() -> str:
	"""Return newline-separated options string for the context_type Select field.

	Called during DocType form load to populate Select options dynamically.
	"""
	contexts = get_timer_context_options()
	options = [""]  # empty = no context
	for ctx in contexts:
		options.append(ctx["doctype"])
	return "\n".join(options)


def get_context_display_value(context_type: str, context_name: str) -> str | None:
	"""Resolve the display value for a context record.

	E.g. context_type="Orga Project", context_name="PROJ-001" → "Website Redesign"
	"""
	if not context_type or not context_name:
		return None

	contexts = get_timer_context_options()
	display_field = "name"
	for ctx in contexts:
		if ctx["doctype"] == context_type:
			display_field = ctx.get("display_field", "name")
			break

	try:
		return frappe.db.get_value(context_type, context_name, display_field)
	except Exception:
		return context_name
