# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.integrations — Slack, Linear, GitHub helpers.

These tests verify message formatting and guard logic without making
real HTTP requests.  External API calls are mocked or skipped.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.integrations import (
	build_slack_message,
	fire_watch_event,
	notify_slack,
)
from watch.tests.test_helpers import ensure_watch_settings


class TestIntegrationsHelpers(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_watch_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	# ── _format_duration (tested indirectly via build_slack_message) ──

	def test_slack_message_basic(self):
		entry = {
			"duration_hours": 1.5,
			"description": "Working on feature",
			"entry_type": "billable",
		}
		msg = build_slack_message(entry)
		self.assertIn("Working on feature", msg)
		self.assertIn("1h 30m", msg)
		self.assertIn("Billable", msg)

	def test_slack_message_zero_duration(self):
		entry = {
			"duration_hours": 0,
			"description": "Quick note",
			"entry_type": "non-billable",
		}
		msg = build_slack_message(entry)
		self.assertIn("0m", msg)

	def test_slack_message_no_description(self):
		entry = {
			"duration_hours": 0.5,
			"description": None,
			"entry_type": "billable",
		}
		msg = build_slack_message(entry)
		# Should have some fallback text
		self.assertTrue(len(msg) > 0)

	def test_slack_message_hours_only(self):
		entry = {
			"duration_hours": 2.0,
			"description": "Two hours",
			"entry_type": "non-billable",
		}
		msg = build_slack_message(entry)
		self.assertIn("2h", msg)

	def test_slack_message_minutes_only(self):
		entry = {
			"duration_hours": 0.25,
			"description": "Quick",
			"entry_type": "non-billable",
		}
		msg = build_slack_message(entry)
		self.assertIn("15m", msg)

	def test_slack_message_non_billable_excluded_from_tags(self):
		"""non-billable entry_type should not appear as a tag."""
		entry = {
			"duration_hours": 1.0,
			"description": "Regular",
			"entry_type": "non-billable",
		}
		msg = build_slack_message(entry)
		self.assertNotIn("[Non-Billable]", msg)
		self.assertNotIn("[non-billable]", msg)

	# ── notify_slack ────────────────────────────────────────────────────

	def test_notify_slack_no_webhook(self):
		"""Should not raise when no webhook is configured."""
		entry = {"duration_hours": 1.0, "description": "test", "entry_type": "billable"}
		# Should silently return — no webhook URL set
		notify_slack(entry)

	@patch("watch.api.integrations.requests.post")
	def test_notify_slack_posts_when_configured(self, mock_post):
		settings = frappe.get_single("Watch Settings")
		settings.slack_webhook_url = "https://hooks.slack.com/test"
		settings.slack_notify_on_stop = 1
		settings.save(ignore_permissions=True)

		try:
			entry = {"duration_hours": 1.0, "description": "test", "entry_type": "billable"}
			notify_slack(entry)
			mock_post.assert_called_once()
		finally:
			settings.slack_webhook_url = ""
			settings.slack_notify_on_stop = 0
			settings.save(ignore_permissions=True)

	# ── fire_watch_event ────────────────────────────────────────────────

	def test_fire_event_no_handlers(self):
		"""Should not raise when no handlers are registered."""
		fire_watch_event("timer_stopped", {"entry_name": "test"})

	# ── test_slack (whitelist) ──────────────────────────────────────────

	def test_test_slack_requires_system_manager(self):
		from watch.api.integrations import test_slack

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			test_slack()
		frappe.set_user("Administrator")

	def test_test_slack_requires_webhook_url(self):
		from watch.api.integrations import test_slack

		settings = frappe.get_single("Watch Settings")
		settings.slack_webhook_url = ""
		settings.save(ignore_permissions=True)

		with self.assertRaises(frappe.exceptions.ValidationError):
			test_slack()

	# ── test_linear (whitelist) ─────────────────────────────────────────

	def test_test_linear_requires_system_manager(self):
		from watch.api.integrations import test_linear

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			test_linear()
		frappe.set_user("Administrator")

	def test_test_linear_requires_api_key(self):
		from watch.api.integrations import test_linear

		frappe.set_user("Administrator")
		settings = frappe.get_single("Watch Settings")
		settings.linear_api_key = ""
		settings.save(ignore_permissions=True)

		with self.assertRaises(frappe.exceptions.ValidationError):
			test_linear()

	# ── test_github (whitelist) ─────────────────────────────────────────

	def test_test_github_requires_system_manager(self):
		from watch.api.integrations import test_github

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			test_github()
		frappe.set_user("Administrator")

	def test_test_github_requires_token(self):
		from watch.api.integrations import test_github

		frappe.set_user("Administrator")
		settings = frappe.get_single("Watch Settings")
		settings.github_token = ""
		settings.save(ignore_permissions=True)

		with self.assertRaises(frappe.exceptions.ValidationError):
			test_github()

	# ── search helpers ──────────────────────────────────────────────────

	def test_search_linear_issues_returns_empty_without_key(self):
		from watch.api.integrations import search_linear_issues

		settings = frappe.get_single("Watch Settings")
		settings.linear_api_key = ""
		settings.save(ignore_permissions=True)

		result = search_linear_issues("test")
		self.assertEqual(result, [])

	def test_search_linear_issues_short_query(self):
		from watch.api.integrations import search_linear_issues

		result = search_linear_issues("a")  # too short
		self.assertEqual(result, [])

	def test_search_github_issues_returns_empty_without_config(self):
		from watch.api.integrations import search_github_issues

		settings = frappe.get_single("Watch Settings")
		settings.github_token = ""
		settings.save(ignore_permissions=True)

		result = search_github_issues("test")
		self.assertEqual(result, [])
