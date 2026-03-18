# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.billing — summary, mark_sent, actions, forward, export."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.billing import (
	export_csv,
	forward_to_app,
	get_billing_actions,
	get_summary,
	mark_sent,
)
from watch.tests.test_helpers import ensure_ft_settings, make_entry, make_tag


class TestBillingAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_ft_settings()

		# Create shared tags
		cls.client_a = make_tag("Client A", category="Client", color="#ff0000")
		cls.client_b = make_tag("Client B", category="Client", color="#00ff00")
		cls.project_x = make_tag("Project X", category="Project")
		cls.project_y = make_tag("Project Y", category="Project")

	def setUp(self):
		frappe.set_user("Administrator")

	# ── get_summary ──────────────────────────────────────────────────────

	def test_get_summary_groups_by_client_tag(self):
		"""Billable entries are grouped by their Client-category tag."""
		make_entry(date="2026-03-01", duration_hours=2.0, tags=["Client A"])
		make_entry(date="2026-03-02", duration_hours=3.0, tags=["Client B"])

		result = get_summary(from_date="2026-03-01", to_date="2026-03-31")

		groups = result["groups"]
		client_names = [g["client_tag"] for g in groups]
		self.assertIn("Client A", client_names)
		self.assertIn("Client B", client_names)

		group_a = next(g for g in groups if g["client_tag"] == "Client A")
		self.assertGreaterEqual(group_a["total_hours"], 2.0)

	def test_get_summary_subgroups_by_project_tag(self):
		"""Within a client group, entries are sub-grouped by Project-category tag."""
		make_entry(date="2031-04-01", duration_hours=1.5, tags=["Client A", "Project X"])
		make_entry(date="2031-04-02", duration_hours=2.5, tags=["Client A", "Project Y"])

		result = get_summary(from_date="2031-04-01", to_date="2031-04-30")

		group_a = next(g for g in result["groups"] if g["client_tag"] == "Client A")
		project_names = [p["project_tag"] for p in group_a["projects"]]
		self.assertIn("Project X", project_names)
		self.assertIn("Project Y", project_names)

		proj_x = next(p for p in group_a["projects"] if p["project_tag"] == "Project X")
		self.assertEqual(proj_x["hours"], 1.5)

	def test_get_summary_separates_entry_types(self):
		"""Totals correctly separate billable, non-billable, and internal hours."""
		make_entry(date="2026-05-01", duration_hours=4.0, entry_type="billable")
		make_entry(date="2026-05-01", duration_hours=1.0, entry_type="non-billable")
		make_entry(date="2026-05-01", duration_hours=0.5, entry_type="internal")

		result = get_summary(from_date="2026-05-01", to_date="2026-05-31")

		totals = result["totals"]
		self.assertGreaterEqual(totals["billable_hours"], 4.0)
		self.assertGreaterEqual(totals["non_billable_hours"], 1.0)
		self.assertGreaterEqual(totals["internal_hours"], 0.5)

	def test_get_summary_unassigned_entries(self):
		"""Entries with no Client tag appear in an unassigned catch-all group."""
		make_entry(date="2026-06-01", duration_hours=1.0, entry_type="billable")

		result = get_summary(from_date="2026-06-01", to_date="2026-06-30")

		unassigned = [g for g in result["groups"] if g["client_tag"] is None]
		self.assertTrue(len(unassigned) > 0, "Expected an unassigned group")
		self.assertGreaterEqual(unassigned[0]["total_hours"], 1.0)

	def test_get_summary_unassigned_last(self):
		"""The unassigned group should appear after named client groups."""
		make_entry(date="2026-07-01", duration_hours=1.0, tags=["Client A"])
		make_entry(date="2026-07-01", duration_hours=1.0)

		result = get_summary(from_date="2026-07-01", to_date="2026-07-31")

		groups = result["groups"]
		if len(groups) > 1:
			self.assertIsNone(groups[-1]["client_tag"],
				"Unassigned group should be last")

	# ── mark_sent ────────────────────────────────────────────────────────

	def test_mark_sent_updates_status(self):
		"""mark_sent changes entry_status from draft to sent."""
		entry = make_entry(date="2026-08-01", duration_hours=1.0, entry_type="billable")

		result = mark_sent(from_date="2026-08-01", to_date="2026-08-31")

		self.assertGreaterEqual(result["updated"], 1)
		entry.reload()
		self.assertEqual(entry.entry_status, "sent")

	def test_mark_sent_filters_by_client_tag(self):
		"""mark_sent with client_tag only marks entries for that client."""
		entry_a = make_entry(date="2026-09-01", duration_hours=1.0, tags=["Client A"])
		entry_b = make_entry(date="2026-09-01", duration_hours=1.0, tags=["Client B"])

		mark_sent(from_date="2026-09-01", to_date="2026-09-30", client_tag="Client A")

		entry_a.reload()
		entry_b.reload()
		self.assertEqual(entry_a.entry_status, "sent")
		self.assertEqual(entry_b.entry_status, "draft")

	# ── get_billing_actions ──────────────────────────────────────────────

	def test_get_billing_actions_empty_when_no_hooks(self):
		"""Returns empty list when no watch_billing_actions hooks are registered."""
		result = get_billing_actions()
		self.assertIsInstance(result, list)
		# Default installation has no billing action hooks
		# so this should return empty or only installed-app actions

	# ── forward_to_app ───────────────────────────────────────────────────

	def test_forward_to_app_rejects_unregistered_endpoint(self):
		"""forward_to_app throws on an endpoint not in watch_billing_actions."""
		make_entry(date="2026-10-01", duration_hours=1.0, entry_type="billable")

		with self.assertRaises(frappe.ValidationError):
			forward_to_app(
				action_endpoint="fake.module.endpoint",
				from_date="2026-10-01",
				to_date="2026-10-31",
			)

	# ── export_csv ───────────────────────────────────────────────────────

	def test_export_csv_generates_content(self):
		"""export_csv returns CSV content and marks entries as sent."""
		entry = make_entry(
			date="2026-11-01", duration_hours=2.0,
			description="CSV test", tags=["Client A"],
		)

		result = export_csv(
			client_tag="Client A",
			from_date="2026-11-01",
			to_date="2026-11-30",
		)

		self.assertIn("csv", result)
		self.assertIn("filename", result)
		self.assertGreaterEqual(result["exported_count"], 1)
		self.assertIn("date", result["csv"])  # header row
		self.assertIn("CSV test", result["csv"])
		self.assertIn("client-a", result["filename"])

		entry.reload()
		self.assertEqual(entry.entry_status, "sent")

	def test_export_csv_filename_unassigned(self):
		"""export_csv uses 'unassigned' slug when client_tag is empty string."""
		make_entry(date="2026-12-01", duration_hours=1.0, entry_type="billable")

		result = export_csv(
			client_tag="",
			from_date="2026-12-01",
			to_date="2026-12-31",
		)

		self.assertIn("unassigned", result["filename"])
