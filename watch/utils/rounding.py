# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Display-only duration rounding.

Raw ``duration_hours`` on Watch Entry is **never** mutated.  Rounding is
applied at read-time in API responses so that summaries and totals show
rounded values while the underlying data stays precise.
"""

import math

import frappe

# Map Select option → minutes
_INCREMENT_MAP = {
	"none": 0,
	"1m": 1,
	"5m": 5,
	"6m": 6,
	"10m": 10,
	"15m": 15,
	"30m": 30,
	"60m": 60,
}


def _get_rounding_config() -> tuple[int, str]:
	"""Return (increment_minutes, direction) from Watch Settings.

	Cached on ``frappe.local`` for the request lifetime.
	"""
	if not hasattr(frappe.local, "_watch_rounding_cache"):
		increment = frappe.db.get_single_value("Watch Settings", "rounding_increment") or "none"
		direction = frappe.db.get_single_value("Watch Settings", "rounding_direction") or "nearest"
		frappe.local._watch_rounding_cache = (_INCREMENT_MAP.get(increment, 0), direction)
	return frappe.local._watch_rounding_cache


def round_hours(hours: float) -> float:
	"""Round *hours* according to Watch Settings.

	Returns the original value unchanged when rounding is disabled (increment == 'none' or 0).
	"""
	if not hours:
		return hours

	increment_minutes, direction = _get_rounding_config()
	if increment_minutes <= 0:
		return hours

	total_minutes = hours * 60
	increment = float(increment_minutes)

	if direction == "up":
		rounded = math.ceil(total_minutes / increment) * increment
	elif direction == "down":
		rounded = math.floor(total_minutes / increment) * increment
	else:  # nearest
		rounded = round(total_minutes / increment) * increment

	return round(rounded / 60, 4)


def round_hours_in_entry(entry: dict) -> dict:
	"""Add ``rounded_duration_hours`` to an entry dict.

	The original ``duration_hours`` is preserved; the rounded value is an
	additional field for display purposes.
	"""
	raw = entry.get("duration_hours") or 0
	entry["rounded_duration_hours"] = round_hours(raw)
	return entry
