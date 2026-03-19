# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.erpnext_bridge — ERPNext sync logic.

These tests mock the bridge as inactive (ERPNext is not installed on the
test site) and verify the guard behaviour.  Full integration tests require
ERPNext installed.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.erpnext_bridge import (
	bulk_sync,
	is_bridge_active,
	sync_day,
	sync_entry,
	test_connection,
)
from watch.tests.test_helpers import ensure_watch_settings, make_entry


class TestERPNextBridge(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_watch_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	# ── is_bridge_active ────────────────────────────────────────────────

	def test_bridge_inactive_without_erpnext(self):
		"""Bridge should be inactive if ERPNext is not installed."""
		result = is_bridge_active()
		# ERPNext is unlikely to be installed on the test site
		if "erpnext" not in frappe.get_installed_apps():
			self.assertFalse(result)

	# ── sync_day ────────────────────────────────────────────────────────

	def test_sync_day_skips_when_inactive(self):
		if "erpnext" in frappe.get_installed_apps():
			self.skipTest("ERPNext installed — skip inactive test")
		result = sync_day("2026-03-13")
		self.assertTrue(result.get("skipped"))
		self.assertEqual(result["reason"], "bridge inactive")

	# ── sync_entry ──────────────────────────────────────────────────────

	def test_sync_entry_skips_when_inactive(self):
		if "erpnext" in frappe.get_installed_apps():
			self.skipTest("ERPNext installed — skip inactive test")
		entry = make_entry(description="bridge test")
		result = sync_entry(entry.name)
		self.assertTrue(result.get("skipped"))

	def test_sync_entry_skips_running_entry(self):
		"""Running entries should not be synced."""
		if "erpnext" in frappe.get_installed_apps():
			# Even with bridge active, running entries are rejected
			entry = make_entry(is_running=1)
			result = sync_entry(entry.name)
			self.assertTrue(result.get("skipped"))
			self.assertEqual(result["reason"], "entry is still running")

	# ── bulk_sync ───────────────────────────────────────────────────────

	def test_bulk_sync_skips_when_inactive(self):
		if "erpnext" in frappe.get_installed_apps():
			self.skipTest("ERPNext installed — skip inactive test")
		result = bulk_sync()
		self.assertTrue(result.get("skipped"))

	# ── test_connection ─────────────────────────────────────────────────

	def test_connection_without_erpnext(self):
		if "erpnext" in frappe.get_installed_apps():
			self.skipTest("ERPNext is installed")
		result = test_connection()
		self.assertFalse(result["ok"])
		self.assertIn("not installed", result["error"])
