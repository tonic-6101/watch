# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.tags."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.tags import (
	archive_tag,
	create_tag,
	delete_tag,
	get_all_budgets,
	get_budget_usage,
	get_tag_stats,
	get_tags,
	merge_tag,
	rename_tag,
	update_tag,
)
from watch.tests.test_helpers import ensure_watch_settings, make_entry, make_tag


class TestTagsAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_watch_settings()

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	# ── create_tag ────────────────────────────────────────────────────────

	def test_create_tag_basic(self):
		"""create_tag returns a dict with the expected fields."""
		result = create_tag(tag_name="Test Create", category="Client", color="#ff0000")
		self.assertEqual(result["tag_name"], "Test Create")
		self.assertEqual(result["category"], "Client")
		self.assertEqual(result["color"], "#ff0000")
		self.assertTrue(frappe.db.exists("Watch Tag", "Test Create"))

	def test_create_tag_duplicate_throws(self):
		"""create_tag raises on duplicate tag_name."""
		make_tag("Duplicate Tag")
		with self.assertRaises(frappe.exceptions.ValidationError):
			create_tag(tag_name="Duplicate Tag")

	# ── get_tags ──────────────────────────────────────────────────────────

	def test_get_tags_filter_by_category(self):
		"""get_tags filters results by category."""
		make_tag("Cat Client A", category="Client")
		make_tag("Cat Project B", category="Project")

		results = get_tags(category="Client")
		tag_names = [t["tag_name"] for t in results]
		self.assertIn("Cat Client A", tag_names)
		self.assertNotIn("Cat Project B", tag_names)

	def test_get_tags_excludes_archived_by_default(self):
		"""Archived tags are excluded unless include_archived is True."""
		tag = make_tag("Archived Tag")
		frappe.db.set_value("Watch Tag", tag.name, "is_archived", 1)

		results = get_tags()
		tag_names = [t["tag_name"] for t in results]
		self.assertNotIn("Archived Tag", tag_names)

		results_all = get_tags(include_archived=True)
		tag_names_all = [t["tag_name"] for t in results_all]
		self.assertIn("Archived Tag", tag_names_all)

	def test_get_tags_search_filter(self):
		"""get_tags search narrows results by substring match."""
		make_tag("Searchable Alpha")
		make_tag("Searchable Beta")
		make_tag("Other Gamma")

		results = get_tags(search="searchable")
		tag_names = [t["tag_name"] for t in results]
		self.assertIn("Searchable Alpha", tag_names)
		self.assertIn("Searchable Beta", tag_names)
		self.assertNotIn("Other Gamma", tag_names)

	def test_get_tags_include_stats(self):
		"""get_tags with include_stats returns entry_count."""
		tag = make_tag("Stats Tag")
		make_entry(tags=[tag.name])
		make_entry(tags=[tag.name])

		results = get_tags(include_stats=True)
		stats_tag = next((t for t in results if t["tag_name"] == "Stats Tag"), None)
		self.assertIsNotNone(stats_tag)
		self.assertEqual(stats_tag["entry_count"], 2)

	# ── rename_tag ────────────────────────────────────────────────────────

	def test_rename_tag_updates_child_rows(self):
		"""rename_tag updates denormalized tag_name on Watch Entry Tag rows."""
		tag = make_tag("Old Name")
		entry = make_entry(tags=[tag.name])

		rename_tag(tag_name="Old Name", new_name="New Name")

		# The Link field (tag) should be updated by frappe.rename_doc
		entry.reload()
		child = entry.tags[0]
		self.assertEqual(child.tag, "New Name")
		# Denormalized tag_name should also be updated
		self.assertEqual(child.tag_name, "New Name")

	# ── merge_tag ─────────────────────────────────────────────────────────

	def test_merge_tag_moves_entries(self):
		"""merge_tag adds target tag to entries that only had source."""
		source = make_tag("Merge Source")
		target = make_tag("Merge Target")
		entry = make_entry(tags=[source.name])

		result = merge_tag(source=source.name, target=target.name)
		self.assertEqual(result["entries_updated"], 1)

		entry.reload()
		entry_tag_links = [t.tag for t in entry.tags]
		self.assertIn(target.name, entry_tag_links)

		# Source should be archived
		source.reload()
		self.assertEqual(source.is_archived, 1)

	def test_merge_tag_no_duplicate_on_shared_entry(self):
		"""merge_tag skips entries that already have the target tag."""
		source = make_tag("Merge Src2")
		target = make_tag("Merge Tgt2")
		# Entry already has both tags
		entry = make_entry(tags=[source.name, target.name])

		result = merge_tag(source=source.name, target=target.name)
		self.assertEqual(result["entries_updated"], 0)

		entry.reload()
		target_count = sum(1 for t in entry.tags if t.tag == target.name)
		self.assertEqual(target_count, 1)

	# ── delete_tag ────────────────────────────────────────────────────────

	def test_delete_tag_blocked_when_in_use(self):
		"""delete_tag raises when tag is used in entries."""
		tag = make_tag("Delete Blocked")
		make_entry(tags=[tag.name])

		with self.assertRaises(frappe.exceptions.ValidationError):
			delete_tag(tag_name=tag.name)

	def test_delete_tag_succeeds_when_unused(self):
		"""delete_tag removes an unused tag."""
		tag = make_tag("Delete OK")
		result = delete_tag(tag_name=tag.name)
		self.assertEqual(result["deleted"], "Delete OK")
		self.assertFalse(frappe.db.exists("Watch Tag", "Delete OK"))

	# ── archive_tag ───────────────────────────────────────────────────────

	def test_archive_tag_toggle(self):
		"""archive_tag sets and clears the is_archived flag."""
		tag = make_tag("Archive Toggle")
		self.assertEqual(tag.is_archived, 0)

		result = archive_tag(tag_name=tag.name, archive=True)
		self.assertEqual(result["is_archived"], 1)

		result = archive_tag(tag_name=tag.name, archive=False)
		self.assertEqual(result["is_archived"], 0)

	# ── get_budget_usage ──────────────────────────────────────────────────

	def test_get_budget_usage_calculation(self):
		"""get_budget_usage sums duration_hours for entries in the given month."""
		tag = make_tag(
			"Budget Tag",
			monthly_hour_budget=20.0,
			budget_warning_threshold=80,
		)
		today = frappe.utils.today()
		month = today[:7]

		make_entry(date=today, duration_hours=5.0, tags=[tag.name])
		make_entry(date=today, duration_hours=3.0, tags=[tag.name])

		result = get_budget_usage(tag_name=tag.name, month=month)
		self.assertEqual(result["budget"], 20.0)
		self.assertAlmostEqual(result["used"], 8.0, places=2)
		self.assertAlmostEqual(result["pct"], 40.0, places=1)
		self.assertEqual(result["status"], "none")

	# ── get_all_budgets ───────────────────────────────────────────────────

	def test_get_all_budgets_only_tags_with_budget(self):
		"""get_all_budgets returns only tags where monthly_hour_budget > 0."""
		tag_with = make_tag("Has Budget", monthly_hour_budget=10.0)
		make_tag("No Budget")

		today = frappe.utils.today()
		month = today[:7]

		result = get_all_budgets(month=month)
		self.assertIn(tag_with.name, result)
		self.assertNotIn("No Budget", result)
		self.assertGreater(result[tag_with.name]["budget"], 0)

	def test_get_budget_usage_approaching_status(self):
		"""get_budget_usage returns 'approaching' when usage crosses the threshold."""
		tag = make_tag(
			"Approaching Budget",
			monthly_hour_budget=10.0,
			budget_warning_threshold=80,
		)
		today = frappe.utils.today()
		month = today[:7]

		make_entry(date=today, duration_hours=9.0, tags=[tag.name])

		result = get_budget_usage(tag_name=tag.name, month=month)
		self.assertEqual(result["status"], "approaching")
		self.assertAlmostEqual(result["pct"], 90.0, places=1)
