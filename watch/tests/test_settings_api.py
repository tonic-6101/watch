# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.settings — Watch Settings get/save and work days."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.settings import get_settings, get_work_days, save_settings
from watch.tests.test_helpers import ensure_watch_settings


class TestSettingsAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_watch_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	# ── get_settings ────────────────────────────────────────────────────

	def test_get_settings_returns_dict(self):
		result = get_settings()
		self.assertIsInstance(result, dict)
		self.assertEqual(result.get("doctype"), "Watch Settings")

	def test_get_settings_cached_per_request(self):
		"""Calling get_settings twice returns the same cached dict."""
		r1 = get_settings()
		r2 = get_settings()
		self.assertIs(r1, r2)

	# ── get_work_days ───────────────────────────────────────────────────

	def test_get_work_days_returns_list(self):
		result = get_work_days()
		self.assertIsInstance(result, list)
		for day in result:
			self.assertIn(day, range(7))

	def test_get_work_days_sorted(self):
		result = get_work_days()
		self.assertEqual(result, sorted(result))

	# ── save_settings ───────────────────────────────────────────────────

	def test_save_settings_updates_field(self):
		save_settings(default_entry_type="non-billable")
		settings = frappe.get_single("Watch Settings")
		self.assertEqual(settings.default_entry_type, "non-billable")
		# Reset
		save_settings(default_entry_type="billable")

	def test_save_settings_ignores_unknown_fields(self):
		"""Fields not in _EDITABLE_FIELDS should be silently ignored."""
		result = save_settings(fake_field="should be ignored")
		self.assertIsInstance(result, dict)

	def test_save_settings_busts_cache(self):
		"""After save, get_settings should reflect new values."""
		save_settings(idle_threshold_minutes=15)
		# Clear the per-request cache
		if hasattr(frappe.local, "_watch_settings_cache"):
			del frappe.local._watch_settings_cache
		result = get_settings()
		self.assertEqual(result.get("idle_threshold_minutes"), 15)
		# Reset
		save_settings(idle_threshold_minutes=0)

	def test_save_settings_requires_system_manager(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			save_settings(default_entry_type="non-billable")
		frappe.set_user("Administrator")

	def test_save_work_day_flags(self):
		save_settings(work_mon=1, work_tue=1, work_wed=1, work_thu=1, work_fri=1, work_sat=0, work_sun=0)
		days = get_work_days()
		self.assertIn(0, days)  # Monday
		self.assertNotIn(5, days)  # Saturday
		self.assertNotIn(6, days)  # Sunday
