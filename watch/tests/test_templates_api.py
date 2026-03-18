# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.templates — favorites and day templates."""

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.templates import (
	apply_day_template,
	delete_template,
	get_day_templates,
	get_favorites,
	reorder_favorites,
	save_day_template,
	save_from_entry,
	update_template,
)
from watch.tests.test_helpers import ensure_ft_settings, make_entry, make_tag


class TestTemplatesAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_ft_settings()

	def setUp(self):
		frappe.set_user("Administrator")

	def _cleanup_templates(self):
		"""Remove all templates for current user."""
		for name in frappe.get_all(
			"FT Entry Template",
			filters={"user": frappe.session.user},
			pluck="name",
		):
			frappe.delete_doc("FT Entry Template", name, ignore_permissions=True)

	# ── get_favorites ───────────────────────────────────────────────────

	def test_get_favorites_empty(self):
		self._cleanup_templates()
		result = get_favorites()
		self.assertIsInstance(result, list)

	# ── save_from_entry ─────────────────────────────────────────────────

	def test_save_from_entry_creates_favorite(self):
		self._cleanup_templates()
		entry = make_entry(description="Favorite task", duration_hours=2.0)
		result = save_from_entry(
			entry_name=entry.name,
			template_name="My Fav",
			slot=1,
		)
		self.assertEqual(result["template_name"], "My Fav")
		self.assertEqual(result["template_type"], "favorite")
		self.assertEqual(len(result["items"]), 1)
		self.assertEqual(result["items"][0]["description"], "Favorite task")

	def test_save_from_entry_without_duration(self):
		self._cleanup_templates()
		entry = make_entry(description="Quick fav", duration_hours=3.5)
		result = save_from_entry(
			entry_name=entry.name,
			template_name="No Duration Fav",
			slot=2,
			keep_duration=False,
		)
		self.assertEqual(result["items"][0]["duration_hours"], 0)

	def test_save_from_entry_with_duration(self):
		self._cleanup_templates()
		entry = make_entry(description="With duration", duration_hours=2.5)
		result = save_from_entry(
			entry_name=entry.name,
			template_name="Keep Duration",
			slot=3,
			keep_duration=True,
		)
		self.assertAlmostEqual(result["items"][0]["duration_hours"], 2.5, places=2)

	def test_save_from_entry_copies_tags(self):
		self._cleanup_templates()
		make_tag("tpl-tag-a")
		entry = make_entry(description="Tagged", tags=["tpl-tag-a"])
		result = save_from_entry(
			entry_name=entry.name,
			template_name="Tagged Fav",
			slot=1,
		)
		self.assertTrue(len(result["items"][0]["tags"]) > 0)

	# ── get_favorites after creating ────────────────────────────────────

	def test_get_favorites_returns_created(self):
		self._cleanup_templates()
		entry = make_entry(description="Fav entry")
		save_from_entry(entry_name=entry.name, template_name="Listed Fav", slot=1)
		result = get_favorites()
		names = [f["template_name"] for f in result]
		self.assertIn("Listed Fav", names)

	# ── save_day_template ───────────────────────────────────────────────

	def test_save_day_template(self):
		self._cleanup_templates()
		e1 = make_entry(description="Morning", duration_hours=2.0)
		e2 = make_entry(description="Afternoon", duration_hours=3.0)

		result = save_day_template(
			date=frappe.utils.today(),
			template_name="Typical Day",
			entry_names=[e1.name, e2.name],
		)
		self.assertEqual(result["template_type"], "day")
		self.assertEqual(len(result["items"]), 2)

	def test_save_day_template_requires_entries(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			save_day_template(
				date=frappe.utils.today(),
				template_name="Empty",
				entry_names=[],
			)

	# ── get_day_templates ───────────────────────────────────────────────

	def test_get_day_templates_includes_stats(self):
		self._cleanup_templates()
		e1 = make_entry(description="Day item", duration_hours=4.0)
		save_day_template(
			date=frappe.utils.today(),
			template_name="Stats Day",
			entry_names=[e1.name],
		)
		result = get_day_templates()
		self.assertTrue(len(result) > 0)
		day = result[0]
		self.assertIn("entry_count", day)
		self.assertIn("total_hours", day)
		self.assertEqual(day["entry_count"], 1)

	# ── apply_day_template ──────────────────────────────────────────────

	def test_apply_day_template_creates_entries(self):
		self._cleanup_templates()
		e1 = make_entry(description="Template item", duration_hours=1.5)
		tpl_result = save_day_template(
			date=frappe.utils.today(),
			template_name="Apply Test",
			entry_names=[e1.name],
		)

		result = apply_day_template(
			template_name=tpl_result["name"],
			date="2026-03-20",
		)
		self.assertEqual(result["count"], 1)
		self.assertEqual(len(result["entries"]), 1)
		self.assertEqual(result["entries"][0]["date"], "2026-03-20")
		self.assertEqual(result["entries"][0]["description"], "Template item")

	# ── update_template ─────────────────────────────────────────────────

	def test_update_template_name(self):
		self._cleanup_templates()
		entry = make_entry(description="Rename test")
		tpl = save_from_entry(entry_name=entry.name, template_name="Old Name", slot=1)

		result = update_template(template_name=tpl["name"], new_name="New Name")
		self.assertEqual(result["template_name"], "New Name")

	def test_update_template_slot(self):
		self._cleanup_templates()
		entry = make_entry(description="Slot test")
		tpl = save_from_entry(entry_name=entry.name, template_name="Slot", slot=1)

		result = update_template(template_name=tpl["name"], slot=5)
		self.assertEqual(result["sort_order"], 5)

	# ── delete_template ─────────────────────────────────────────────────

	def test_delete_template(self):
		self._cleanup_templates()
		entry = make_entry(description="Delete me")
		tpl = save_from_entry(entry_name=entry.name, template_name="Doomed", slot=1)

		result = delete_template(tpl["name"])
		self.assertEqual(result["deleted"], tpl["name"])
		self.assertFalse(frappe.db.exists("FT Entry Template", tpl["name"]))

	# ── reorder_favorites ───────────────────────────────────────────────

	def test_reorder_favorites(self):
		self._cleanup_templates()
		e1 = make_entry(description="First")
		e2 = make_entry(description="Second")
		t1 = save_from_entry(entry_name=e1.name, template_name="Fav A", slot=1)
		t2 = save_from_entry(entry_name=e2.name, template_name="Fav B", slot=2)

		# Reverse order
		result = reorder_favorites(order=[t2["name"], t1["name"]])
		self.assertEqual(result["reordered"], 2)

		doc1 = frappe.get_doc("FT Entry Template", t1["name"])
		doc2 = frappe.get_doc("FT Entry Template", t2["name"])
		self.assertEqual(doc2.sort_order, 1)
		self.assertEqual(doc1.sort_order, 2)
