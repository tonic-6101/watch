# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


_WORK_DAY_MAP = {
	"work_mon": 0,
	"work_tue": 1,
	"work_wed": 2,
	"work_thu": 3,
	"work_fri": 4,
	"work_sat": 5,
	"work_sun": 6,
}

_EDITABLE_FIELDS = [
	"default_entry_type",
	"lock_entries_older_than",
	"auto_stop_timer_after",
	"work_mon", "work_tue", "work_wed", "work_thu", "work_fri", "work_sat", "work_sun",
	"idle_threshold_minutes",
	"daily_nudge_after",
	"budget_warning_threshold",
	"enable_erpnext_bridge",
	"sync_mode",
	"sync_interval",
	"erpnext_site_url",
	"default_activity_type",
	"sync_billable_only",
	"map_project_tags",
	"slack_webhook_url",
	"slack_notify_on_stop",
	"slack_message_template",
	"linear_api_key",
	"linear_post_comment",
	"github_token",
	"github_default_repo",
	"github_post_comment",
]


@frappe.whitelist()
def get_settings() -> dict:
	"""
	Return FT Settings as a dict.  Cached on frappe.local for the lifetime of
	the request so multiple components can call this without repeated DB hits.
	"""
	if not hasattr(frappe.local, "_ft_settings_cache"):
		frappe.local._ft_settings_cache = frappe.get_single("FT Settings").as_dict()
	return frappe.local._ft_settings_cache


@frappe.whitelist()
def get_work_days() -> list:
	"""
	Return a sorted list of weekday integers (0 = Mon … 6 = Sun) that are
	marked as work days in FT Settings.
	"""
	s = frappe.get_single("FT Settings")
	return sorted(v for k, v in _WORK_DAY_MAP.items() if s.get(k))


@frappe.whitelist()
def save_settings(**kwargs) -> dict:
	"""
	Persist FT Settings.  Only System Manager may call this.
	Ignores any keys that are not in the allowed editable field list.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw(_("Only System Manager can change FT Settings"), frappe.PermissionError)

	settings = frappe.get_single("FT Settings")

	for field in _EDITABLE_FIELDS:
		if field in kwargs:
			settings.set(field, kwargs[field])

	settings.save()

	# Bust the per-request cache so subsequent get_settings() calls see new values
	if hasattr(frappe.local, "_ft_settings_cache"):
		del frappe.local._ft_settings_cache

	return settings.as_dict()
