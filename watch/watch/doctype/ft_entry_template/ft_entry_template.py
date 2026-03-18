# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class FTEntryTemplate(Document):
	def validate(self):
		self._enforce_user()
		self._validate_sort_order()
		self._validate_favorite_limit()

	def _enforce_user(self):
		"""Auto-set user on insert; prevent changing owner after creation."""
		if self.is_new():
			self.user = frappe.session.user
		elif self.user != frappe.session.user and "System Manager" not in frappe.get_roles():
			frappe.throw(_("Not permitted"), frappe.PermissionError)

	def _validate_sort_order(self):
		if self.template_type == "favorite":
			if not (1 <= (self.sort_order or 0) <= 9):
				frappe.throw(_("Favorite slot must be between 1 and 9."))
			# Check for duplicate slot for this user
			existing = frappe.db.get_value(
				"FT Entry Template",
				{
					"user": self.user,
					"template_type": "favorite",
					"sort_order": self.sort_order,
					"name": ["!=", self.name],
				},
				"name",
			)
			if existing:
				frappe.throw(_("Slot {0} is already used by another favorite.").format(self.sort_order))
		else:
			self.sort_order = 0

	def _validate_favorite_limit(self):
		if self.template_type == "favorite" and self.is_new():
			count = frappe.db.count(
				"FT Entry Template",
				{"user": self.user, "template_type": "favorite"},
			)
			if count >= 9:
				frappe.throw(_("Maximum 9 favorites allowed."))
