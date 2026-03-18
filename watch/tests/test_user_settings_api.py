# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.user_settings — per-user preferences and extension tokens."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.user_settings import (
	generate_extension_token,
	get_preferences,
	revoke_extension_token,
	save_preferences,
)
from watch.tests.test_helpers import ensure_ft_settings


class TestUserSettingsAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_ft_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	# ── get_preferences ─────────────────────────────────────────────────

	def test_get_preferences_creates_if_missing(self):
		"""Should auto-create FT User Settings if none exists."""
		result = get_preferences()
		self.assertIsInstance(result, dict)
		self.assertEqual(result.get("doctype"), "FT User Settings")
		self.assertEqual(result.get("user"), "Administrator")

	def test_get_preferences_returns_existing(self):
		get_preferences()  # ensure created
		result = get_preferences()
		self.assertEqual(result["user"], "Administrator")

	# ── save_preferences ────────────────────────────────────────────────

	def test_save_weekly_hour_target(self):
		result = save_preferences(weekly_hour_target=40)
		self.assertEqual(result["weekly_hour_target"], 40)

		doc = frappe.get_doc("FT User Settings", "Administrator")
		self.assertEqual(doc.weekly_hour_target, 40)

	def test_save_focus_settings(self):
		result = save_preferences(
			focus_work_minutes=25,
			focus_break_minutes=5,
			focus_sessions=4,
		)
		self.assertEqual(result["focus_work_minutes"], 25)
		self.assertEqual(result["focus_break_minutes"], 5)
		self.assertEqual(result["focus_sessions"], 4)

	def test_save_ignores_unknown_fields(self):
		result = save_preferences(nonexistent_field="ignored")
		self.assertNotIn("nonexistent_field", result)

	def test_save_keyboard_shortcuts(self):
		result = save_preferences(enable_keyboard_shortcuts=1)
		self.assertEqual(result["enable_keyboard_shortcuts"], 1)

	# ── extension tokens ────────────────────────────────────────────────

	def test_generate_token_returns_token_string(self):
		result = generate_extension_token()
		self.assertIn("token", result)
		self.assertIn(":", result["token"])
		self.assertEqual(result["extension_token_active"], 1)

	def test_generate_token_marks_active(self):
		generate_extension_token()
		doc = frappe.get_doc("FT User Settings", "Administrator")
		self.assertEqual(doc.extension_token_active, 1)

	def test_revoke_token(self):
		generate_extension_token()
		result = revoke_extension_token()
		self.assertEqual(result["extension_token_active"], 0)

		doc = frappe.get_doc("FT User Settings", "Administrator")
		self.assertEqual(doc.extension_token_active, 0)

	def test_revoke_clears_api_key(self):
		generate_extension_token()
		revoke_extension_token()
		user_doc = frappe.get_doc("User", "Administrator")
		self.assertFalse(user_doc.api_key)

	def test_regenerate_token_changes_key(self):
		r1 = generate_extension_token()
		r2 = generate_extension_token()
		self.assertNotEqual(r1["token"], r2["token"])
