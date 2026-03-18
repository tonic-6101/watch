# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.translate import get_messages_for_boot

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access Watch"), frappe.PermissionError)

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()

	context.boot = get_boot()
	context.boot.csrf_token = csrf_token
	context.csrf_token = csrf_token
	context.site_name = frappe.local.site
	context.title = "Watch"
	context.description = "Time tracking"

	return context


@frappe.whitelist(methods=["POST"])
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(_("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	user = frappe.session.user
	user_info = frappe.get_doc("User", user)

	boot = {
		"user": {
			"name": user,
			"email": user_info.email or "",
			"full_name": user_info.full_name or user,
			"user_image": user_info.user_image or "",
		},
		"user_roles": frappe.get_roles(user),
	}

	# Inject Dock boot data so the SPA can detect Dock and use DockNavbar
	dock_boot = _get_dock_boot()
	if dock_boot:
		boot["dock"] = dock_boot

	return frappe._dict(
		{
			"frappe": {
				"boot": boot,
				"csrf_token": frappe.sessions.get_csrf_token(),
			},
			"frappe_version": frappe.__version__,
			"default_route": "/watch",
			"site_name": frappe.local.site,
			"read_only_mode": frappe.flags.read_only,
			"lang": frappe.local.lang,
			"__messages": get_messages_for_boot(),
		}
	)


def _get_dock_boot():
	"""Return Dock boot data if Dock is installed, else None."""
	if "dock" not in frappe.get_installed_apps():
		return None
	try:
		from dock.boot import get_boot as dock_get_boot
		return dock_get_boot()
	except Exception:
		return None
