# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.search."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.search import (
	navigation_shortcuts,
	search_entries,
	search_tags,
	timer_action,
)
from watch.tests.test_helpers import (
	cleanup_timer,
	ensure_watch_settings,
	make_entry,
	make_tag,
)


class TestSearchAPI(FrappeTestCase):
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

	# ── search_entries ────────────────────────────────────────────────────

	def test_search_entries_empty_query(self):
		"""Empty or short queries return no results."""
		self.assertEqual(search_entries(""), [])
		self.assertEqual(search_entries("a"), [])

	def test_search_entries_finds_match(self):
		"""Full-text search matches on description."""
		entry = make_entry(description="deploy production server")
		results = search_entries("deploy")
		labels = [r["label"] for r in results]
		self.assertIn("deploy production server", labels)
		# Verify result structure
		match = next(r for r in results if r["label"] == "deploy production server")
		self.assertEqual(match["meta"], "entry")
		self.assertIn("/watch/", match["route"])
		self.assertEqual(match["icon"], "clock")

	def test_search_entries_no_match(self):
		"""Non-matching query returns empty."""
		make_entry(description="unrelated task")
		results = search_entries("xyznonexistent")
		self.assertEqual(results, [])

	def test_search_entries_includes_tag_info(self):
		"""Search results include tag information in description."""
		tag = make_tag("SearchClient", category="Client")
		make_entry(description="client meeting notes", tags=[tag.name])
		results = search_entries("client meeting")
		self.assertTrue(len(results) > 0)
		match = results[0]
		self.assertIn("SearchClient", match["description"])

	def test_search_entries_limit(self):
		"""Results are limited to 8."""
		for i in range(12):
			make_entry(description=f"searchlimit task {i}")
		results = search_entries("searchlimit")
		self.assertLessEqual(len(results), 8)

	def test_search_entries_user_scoped(self):
		"""Only returns entries for current user."""
		make_entry(description="other user entry", user="Guest")
		frappe.set_user("Administrator")
		results = search_entries("other user entry")
		# Administrator should not see Guest's entries
		labels = [r["label"] for r in results]
		self.assertNotIn("other user entry", labels)

	# ── search_tags ──────────────────────────────────────────────────────

	def test_search_tags_empty_query(self):
		"""Empty query returns no results."""
		self.assertEqual(search_tags(""), [])

	def test_search_tags_finds_match(self):
		"""Tag search matches on tag_name."""
		make_tag("SearchTagAlpha", category="Project")
		results = search_tags("SearchTagAlpha")
		labels = [r["label"] for r in results]
		self.assertIn("SearchTagAlpha", labels)

	def test_search_tags_result_structure(self):
		"""Verify tag search result structure."""
		make_tag("SearchTagBeta", category="Client")
		results = search_tags("SearchTagBeta")
		self.assertTrue(len(results) > 0)
		match = next(r for r in results if r["label"] == "SearchTagBeta")
		self.assertEqual(match["icon"], "tag")
		self.assertEqual(match["meta"], "tag")
		self.assertIn("Client", match["description"])

	def test_search_tags_client_routes_to_prepare(self):
		"""Client tags route to prepare summary."""
		make_tag("SearchClient2", category="Client")
		results = search_tags("SearchClient2")
		match = next(r for r in results if r["label"] == "SearchClient2")
		self.assertIn("/watch/prepare", match["route"])

	def test_search_tags_non_client_routes_to_tags(self):
		"""Non-client tags route to tag management."""
		make_tag("SearchProject2", category="Project")
		results = search_tags("SearchProject2")
		match = next(r for r in results if r["label"] == "SearchProject2")
		self.assertEqual(match["route"], "/watch/tags")

	def test_search_tags_limit(self):
		"""Tag results are limited to 6."""
		for i in range(10):
			make_tag(f"LimitTag{i:02d}")
		results = search_tags("LimitTag")
		self.assertLessEqual(len(results), 6)

	# ── timer_action ─────────────────────────────────────────────────────

	def test_timer_action_empty_query(self):
		"""Empty query returns no results."""
		self.assertEqual(timer_action(""), [])

	def test_timer_action_returns_start_hint(self):
		"""Non-empty query returns a start timer action."""
		cleanup_timer()
		results = timer_action("fix login bug")
		self.assertEqual(len(results), 1)
		result = results[0]
		self.assertEqual(result["meta"], "action")
		self.assertIn("fix login bug", result["label"])
		self.assertEqual(result["action"], "watch.api.timer.start_timer")
		self.assertEqual(result["action_args"]["description"], "fix login bug")

	def test_timer_action_running_timer_label(self):
		"""When timer is running, label says 'Stop current & start'."""
		from watch.api.timer import start_timer, stop_timer
		cleanup_timer()
		start_timer(description="existing task")
		try:
			results = timer_action("new task")
			self.assertTrue(len(results) > 0)
			self.assertIn("Stop current", results[0]["label"])
		finally:
			stop_timer()

	# ── navigation_shortcuts ─────────────────────────────────────────────

	def test_navigation_empty_query(self):
		"""Empty query returns no results."""
		self.assertEqual(navigation_shortcuts(""), [])

	def test_navigation_today(self):
		"""'today' matches the daily view shortcut."""
		results = navigation_shortcuts("today")
		self.assertTrue(len(results) > 0)
		labels = [r["label"] for r in results]
		self.assertIn("Today", labels)

	def test_navigation_week(self):
		"""'week' matches the weekly view shortcut."""
		results = navigation_shortcuts("week")
		self.assertTrue(len(results) > 0)
		match = next(r for r in results if r["label"] == "Week")
		self.assertEqual(match["meta"], "nav")
		self.assertIn("/watch/week", match["route"])

	def test_navigation_range(self):
		"""'range' matches the date range report shortcut."""
		results = navigation_shortcuts("range")
		self.assertTrue(len(results) > 0)
		match = next(r for r in results if r["label"] == "Range")
		self.assertEqual(match["route"], "/watch/range")

	def test_navigation_prepare(self):
		"""'prepare' matches the prepare summary shortcut."""
		results = navigation_shortcuts("prepare")
		self.assertTrue(len(results) > 0)
		labels = [r["label"] for r in results]
		self.assertIn("Prepare", labels)

	def test_navigation_settings(self):
		"""'settings' matches the settings shortcut."""
		results = navigation_shortcuts("settings")
		self.assertTrue(len(results) > 0)
		labels = [r["label"] for r in results]
		self.assertIn("Settings", labels)

	def test_navigation_tags(self):
		"""'tags' matches the tag management shortcut."""
		results = navigation_shortcuts("tags")
		self.assertTrue(len(results) > 0)
		labels = [r["label"] for r in results]
		self.assertIn("Tags", labels)

	def test_navigation_partial_match(self):
		"""Partial keyword matches work."""
		results = navigation_shortcuts("set")
		labels = [r["label"] for r in results]
		self.assertIn("Settings", labels)

	def test_navigation_limit(self):
		"""Navigation results are limited to 3."""
		# 'e' should match multiple items (entries, week, prepare, settings, etc.)
		results = navigation_shortcuts("e")
		self.assertLessEqual(len(results), 3)
