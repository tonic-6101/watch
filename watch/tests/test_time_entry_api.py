# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.time_entry — manual entry CRUD, summaries, bulk ops."""

from datetime import date, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.time_entry import (
	bulk_add_tag,
	bulk_delete,
	bulk_set_entry_type,
	create_entry,
	delete_entry,
	duplicate_entry,
	get_daily_summary,
	get_weekly_chart_data,
	get_weekly_summary,
	update_entry,
)
from watch.tests.test_helpers import ensure_watch_settings, make_entry, make_tag


class TestTimeEntryAPI(FrappeTestCase):

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_watch_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		# Reset soft lock so it doesn't leak into other tests.
		settings = frappe.get_single("Watch Settings")
		settings.lock_entries_older_than = 0
		settings.save(ignore_permissions=True)

	# ── create_entry ──────────────────────────────────────────────────────

	def test_create_entry_basic(self):
		today = frappe.utils.today()
		result = create_entry(date=today, duration_hours=2.5, description="Basic test")
		self.assertEqual(result["date"], today)
		self.assertAlmostEqual(result["duration_hours"], 2.5)
		self.assertEqual(result["description"], "Basic test")
		self.assertEqual(result["entry_type"], "billable")
		self.assertEqual(result["is_running"], 0)

	def test_create_entry_with_tags(self):
		tag = make_tag("TestClient", category="Client", color="#ff0000")
		today = frappe.utils.today()
		result = create_entry(date=today, duration_hours=1.0, tags=[tag.name])
		self.assertIn(tag.tag_name, result["tag_names"])
		self.assertEqual(len(result["tag_meta"]), 1)
		self.assertEqual(result["tag_meta"][0]["color"], "#ff0000")

	def test_create_entry_with_all_fields(self):
		tag = make_tag("FullFieldTag")
		today = frappe.utils.today()
		result = create_entry(
			date=today,
			duration_hours=1.5,
			start_time="09:00:00",
			end_time="10:30:00",
			description="Full field test",
			entry_type="non-billable",
			tags=[tag.name],
			linear_issue="LIN-123",
			github_ref="org/repo#42",
		)
		self.assertEqual(result["entry_type"], "non-billable")
		self.assertEqual(result["linear_issue"], "LIN-123")
		self.assertEqual(result["github_ref"], "org/repo#42")

	def test_create_entry_soft_lock_blocks_old_date(self):
		settings = frappe.get_single("Watch Settings")
		settings.lock_entries_older_than = 7
		settings.save(ignore_permissions=True)

		old_date = str(date.today() - timedelta(days=30))
		with self.assertRaises(frappe.exceptions.ValidationError):
			create_entry(date=old_date, duration_hours=1.0)

	def test_create_entry_soft_lock_allows_recent_date(self):
		settings = frappe.get_single("Watch Settings")
		settings.lock_entries_older_than = 7
		settings.save(ignore_permissions=True)

		recent = str(date.today() - timedelta(days=3))
		result = create_entry(date=recent, duration_hours=1.0)
		self.assertEqual(result["date"], recent)

	# ── update_entry ──────────────────────────────────────────────────────

	def test_update_entry_basic(self):
		entry = make_entry(description="Before update")
		result = update_entry(entry_name=entry.name, description="After update", duration_hours=3.0)
		self.assertEqual(result["description"], "After update")
		self.assertAlmostEqual(result["duration_hours"], 3.0)

	def test_update_entry_blocks_sent(self):
		entry = make_entry(entry_status="sent")
		with self.assertRaises(frappe.exceptions.ValidationError):
			update_entry(entry_name=entry.name, description="Should fail")

	def test_update_entry_checks_ownership(self):
		entry = make_entry(user="Administrator")
		# Create a non-admin user context
		test_user = "test_watch_user@example.com"
		if not frappe.db.exists("User", test_user):
			frappe.get_doc({
				"doctype": "User",
				"email": test_user,
				"first_name": "Test",
				"user_type": "Website User",
			}).insert(ignore_permissions=True)

		frappe.set_user(test_user)
		with self.assertRaises(frappe.exceptions.PermissionError):
			update_entry(entry_name=entry.name, description="Not my entry")
		frappe.set_user("Administrator")

	# ── delete_entry ──────────────────────────────────────────────────────

	def test_delete_entry_basic(self):
		entry = make_entry(description="To be deleted")
		result = delete_entry(entry_name=entry.name)
		self.assertEqual(result["deleted"], entry.name)
		self.assertFalse(frappe.db.exists("Watch Entry", entry.name))

	def test_delete_entry_blocks_running(self):
		entry = make_entry(is_running=1)
		with self.assertRaises(frappe.exceptions.ValidationError):
			delete_entry(entry_name=entry.name)

	def test_delete_entry_blocks_sent(self):
		entry = make_entry(entry_status="sent")
		with self.assertRaises(frappe.exceptions.ValidationError):
			delete_entry(entry_name=entry.name)

	# ── get_daily_summary ─────────────────────────────────────────────────

	def test_daily_summary_totals(self):
		# Use a future date with no pre-existing entries
		test_date = "2030-06-15"
		make_entry(date=test_date, duration_hours=2.0, entry_type="billable")
		make_entry(date=test_date, duration_hours=1.5, entry_type="non-billable")
		make_entry(date=test_date, duration_hours=0.5, entry_type="billable")

		result = get_daily_summary(date=test_date)
		self.assertEqual(result["date"], test_date)
		self.assertAlmostEqual(result["total_hours"], 4.0, places=2)
		self.assertAlmostEqual(result["billable_hours"], 2.5, places=2)
		self.assertEqual(len(result["entries"]), 3)

	# ── get_weekly_summary ────────────────────────────────────────────────

	def test_weekly_summary_groups_by_day(self):
		# Use a far-future week with no pre-existing entries
		monday = date(2031, 1, 6)  # A Monday

		make_entry(date=str(monday), duration_hours=3.0)
		make_entry(date=str(monday + timedelta(days=2)), duration_hours=2.0, entry_type="non-billable")

		result = get_weekly_summary(week_start=str(monday))
		self.assertEqual(len(result["days"]), 7)
		self.assertEqual(result["week_start"], str(monday))
		self.assertAlmostEqual(result["total_hours"], 5.0, places=2)
		self.assertAlmostEqual(result["billable_hours"], 3.0, places=2)
		self.assertIn("prev_week_total_hours", result)
		self.assertIn("work_days", result)

		monday_day = next(d for d in result["days"] if d["date"] == str(monday))
		self.assertGreaterEqual(monday_day["entry_count"], 1)

	# ── duplicate_entry ───────────────────────────────────────────────────

	def test_duplicate_same_day_keeps_times(self):
		entry = make_entry(start_time="09:00:00", end_time="10:30:00", duration_hours=1.5)
		result = duplicate_entry(entry_name=entry.name, target_date=str(entry.date))
		self.assertIsNotNone(result["start_time"])
		self.assertIsNotNone(result["end_time"])
		self.assertAlmostEqual(result["duration_hours"], 1.5)
		self.assertNotEqual(result["name"], entry.name)

	def test_duplicate_cross_day_drops_times(self):
		today = date.today()
		tomorrow = str(today + timedelta(days=1))
		entry = make_entry(date=str(today), start_time="09:00:00", end_time="10:30:00", duration_hours=1.5)
		result = duplicate_entry(entry_name=entry.name, target_date=tomorrow)
		self.assertEqual(result["date"], tomorrow)
		# Duration should be preserved even though time slots are not copied
		self.assertAlmostEqual(result["duration_hours"], 1.5)

	def test_duplicate_copies_tags(self):
		tag = make_tag("DupTag")
		entry = make_entry(tags=[tag.name])
		result = duplicate_entry(entry_name=entry.name, target_date=str(entry.date))
		self.assertIn(tag.tag_name, result["tag_names"])

	# ── bulk_add_tag ──────────────────────────────────────────────────────

	def test_bulk_add_tag_basic(self):
		tag = make_tag("BulkTag")
		e1 = make_entry(description="Bulk 1")
		e2 = make_entry(description="Bulk 2")

		result = bulk_add_tag(entry_names=[e1.name, e2.name], tag=tag.name)
		self.assertEqual(result["updated"], 2)
		self.assertEqual(result["skipped"], 0)

	def test_bulk_add_tag_skips_sent(self):
		tag = make_tag("BulkTagSent")
		e1 = make_entry(description="Draft one")
		e2 = make_entry(description="Sent one", entry_status="sent")

		result = bulk_add_tag(entry_names=[e1.name, e2.name], tag=tag.name)
		self.assertEqual(result["updated"], 1)
		self.assertEqual(result["skipped"], 1)

	# ── bulk_set_entry_type ───────────────────────────────────────────────

	def test_bulk_set_entry_type(self):
		e1 = make_entry(entry_type="billable")
		e2 = make_entry(entry_type="billable")
		e3 = make_entry(entry_type="billable", entry_status="sent")

		result = bulk_set_entry_type(entry_names=[e1.name, e2.name, e3.name], entry_type="non-billable")
		self.assertEqual(result["updated"], 2)
		self.assertEqual(result["skipped"], 1)

		# Verify the change persisted
		e1.reload()
		self.assertEqual(e1.entry_type, "non-billable")

	# ── bulk_delete ───────────────────────────────────────────────────────

	def test_bulk_delete_skips_running_and_sent(self):
		e_draft = make_entry(description="Deletable")
		e_running = make_entry(description="Running", is_running=1)
		e_sent = make_entry(description="Sent", entry_status="sent")

		result = bulk_delete(entry_names=[e_draft.name, e_running.name, e_sent.name])
		self.assertEqual(result["deleted"], 1)
		self.assertEqual(result["skipped"], 2)
		self.assertFalse(frappe.db.exists("Watch Entry", e_draft.name))
		self.assertTrue(frappe.db.exists("Watch Entry", e_running.name))
		self.assertTrue(frappe.db.exists("Watch Entry", e_sent.name))

	# ── get_weekly_chart_data ─────────────────────────────────────────────

	def test_weekly_chart_data_structure(self):
		monday = date(2030, 6, 17)  # A future Monday

		tag = make_tag("ChartTag", category="Client", color="#3b82f6")
		make_entry(date=str(monday), duration_hours=2.0, tags=[tag.name])
		make_entry(date=str(monday + timedelta(days=1)), duration_hours=1.0)

		result = get_weekly_chart_data(week_start=str(monday))

		self.assertEqual(len(result["daily"]), 7)
		self.assertIn("tags", result)
		self.assertIn("total_hours", result)
		self.assertGreaterEqual(result["total_hours"], 3.0)

		# Monday should have hours
		mon = result["daily"][0]
		self.assertEqual(mon["label"], "Mo")
		self.assertGreaterEqual(mon["hours"], 2.0)

		# Tags breakdown should include our tag
		tag_names = [t["tag_name"] for t in result["tags"]]
		self.assertIn("ChartTag", tag_names)

	def test_weekly_chart_data_untagged_bucket(self):
		monday = date(2030, 6, 24)  # Another future Monday

		make_entry(date=str(monday), duration_hours=1.0, tags=[])

		result = get_weekly_chart_data(week_start=str(monday))
		untagged = [t for t in result["tags"] if t["tag_name"] is None]
		self.assertGreaterEqual(len(untagged), 1)
		self.assertGreaterEqual(untagged[0]["hours"], 1.0)
