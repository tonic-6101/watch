# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import math

ROUNDING_MINUTES = {
	"none":  None,
	"6min":  6,
	"10min": 10,
	"15min": 15,
	"30min": 30,
	"60min": 60,
}


def round_up_hours(duration_hours: float, rule: str) -> float:
	"""Round duration_hours up to the nearest increment defined by rule."""
	minutes = ROUNDING_MINUTES.get(rule)
	if not minutes:
		return duration_hours
	total_minutes = duration_hours * 60
	rounded = math.ceil(total_minutes / minutes) * minutes
	return round(rounded / 60, 4)


def get_billing_duration(entry, settings=None) -> float:
	"""
	Return the effective billing duration for an entry.

	Accepts either:
	  - a Frappe Document with .tags child table (each row has .tag FK to FT Tag)
	  - a dict enriched with tag_names (list of str) via _attach_tags / _attach_tag_meta

	Priority chain:
	  1. entry_rounding_override → exact duration_hours
	  2. First tag with a non-none rounding_rule
	  3. FT Settings.rounding_rule (site-wide fallback)
	  4. none → exact duration_hours
	"""
	import frappe

	if hasattr(entry, "duration_hours"):
		duration = float(entry.duration_hours or 0)
		override = bool(entry.entry_rounding_override)
	else:
		duration = float(entry.get("duration_hours") or 0)
		override = bool(entry.get("entry_rounding_override"))

	if override:
		return duration

	# Resolve tag names from document or dict
	if hasattr(entry, "tags"):
		tag_names = [row.tag for row in entry.tags if row.tag]
	else:
		tag_names = entry.get("tag_names") or []

	rule = "none"
	for tag_name in tag_names:
		if not tag_name:
			continue
		try:
			tag_doc = frappe.get_cached_doc("FT Tag", tag_name)
			if tag_doc.rounding_rule and tag_doc.rounding_rule != "none":
				rule = tag_doc.rounding_rule
				break
		except Exception:
			continue

	if rule == "none":
		if settings is None:
			settings = frappe.get_single("FT Settings")
		rule = getattr(settings, "rounding_rule", None) or "none"

	return round_up_hours(duration, rule)
