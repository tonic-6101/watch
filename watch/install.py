# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe


def after_install():
	_create_role()
	_assign_role_to_existing_users()


def assign_time_tracker_role(doc, method=None):
	"""Auto-assign Time Tracker role to newly created users.

	Called via doc_events -> User -> after_insert (see hooks.py).
	"""
	if doc.user_type != "System User":
		return

	if not any(r.role == "Time Tracker" for r in doc.roles):
		doc.append("roles", {"role": "Time Tracker"})
		doc.save(ignore_permissions=True)


def _create_role():
	"""Create the Time Tracker role if it doesn't exist."""
	if not frappe.db.exists("Role", "Time Tracker"):
		role = frappe.new_doc("Role")
		role.role_name = "Time Tracker"
		role.desk_access = 1
		role.is_custom = 0
		role.insert(ignore_permissions=True)


def _assign_role_to_existing_users():
	"""Assign Time Tracker role to all active System Users."""
	users = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"name": ["not in", ["Administrator", "Guest"]],
		},
		pluck="name",
	)

	for user_name in users:
		user = frappe.get_doc("User", user_name)
		if not any(r.role == "Time Tracker" for r in user.roles):
			user.append("roles", {"role": "Time Tracker"})
			user.save(ignore_permissions=True)

	# Handle Administrator separately (always gets the role)
	if frappe.db.exists("User", "Administrator"):
		admin = frappe.get_doc("User", "Administrator")
		if not any(r.role == "Time Tracker" for r in admin.roles):
			admin.append("roles", {"role": "Time Tracker"})
			admin.save(ignore_permissions=True)

	frappe.db.commit()
