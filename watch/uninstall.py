# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe


def after_uninstall():
	_remove_roles()


def _remove_roles():
	"""Remove the Time Tracker role created during install."""
	if frappe.db.exists("Role", "Time Tracker"):
		frappe.delete_doc("Role", "Time Tracker", force=True)
		frappe.db.commit()
