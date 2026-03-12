# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


_EDITABLE_FIELDS = [
	"weekly_hour_target",
	"enable_keyboard_shortcuts",
	"focus_work_minutes",
	"focus_break_minutes",
	"focus_sessions",
]


def _get_or_create(user: str) -> "frappe.Document":
	"""Return the FT User Settings for *user*, creating it lazily if needed."""
	if frappe.db.exists("FT User Settings", user):
		return frappe.get_doc("FT User Settings", user)

	doc = frappe.new_doc("FT User Settings")
	doc.user = user
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist()
def get_preferences() -> dict:
	"""Return the current user's FT User Settings (creates record if missing)."""
	doc = _get_or_create(frappe.session.user)
	return doc.as_dict()


@frappe.whitelist()
def save_preferences(**kwargs) -> dict:
	"""Upsert FT User Settings for the current user.

	Only fields in ``_EDITABLE_FIELDS`` are accepted; everything else is
	silently ignored.
	"""
	doc = _get_or_create(frappe.session.user)

	for field in _EDITABLE_FIELDS:
		if field in kwargs:
			doc.set(field, kwargs[field])

	doc.save(ignore_permissions=True)
	return doc.as_dict()


@frappe.whitelist()
def generate_extension_token() -> dict:
	"""Generate an API key/secret pair for the browser extension.

	Uses Frappe's built-in ``generate_keys`` on the User record.
	The secret is returned **once only** — it is stored hashed and cannot
	be retrieved later.  Sets ``extension_token_active = 1`` on
	FT User Settings.

	If a token already exists, regenerating will invalidate the old one.
	"""
	user = frappe.session.user
	user_doc = frappe.get_doc("User", user)

	# generate_keys creates api_key + api_secret on the User record
	api_secret = user_doc.get_password("api_secret") if user_doc.api_key else None

	# Always regenerate — this invalidates any previous key
	api_secret = frappe.generate_hash(length=15)
	user_doc.api_key = frappe.generate_hash(length=15)
	user_doc.api_secret = api_secret
	user_doc.save(ignore_permissions=True)

	# Mark token as active in FT User Settings
	doc = _get_or_create(user)
	doc.extension_token_active = 1
	doc.save(ignore_permissions=True)

	token = f"{user_doc.api_key}:{api_secret}"
	return {"token": token, "extension_token_active": 1}


@frappe.whitelist()
def revoke_extension_token() -> dict:
	"""Revoke the browser extension token.

	Clears api_key and api_secret on the User record so that any
	subsequent API call with the old token returns 401.
	Sets ``extension_token_active = 0``.
	"""
	user = frappe.session.user
	user_doc = frappe.get_doc("User", user)

	user_doc.api_key = ""
	user_doc.api_secret = ""
	user_doc.save(ignore_permissions=True)

	doc = _get_or_create(user)
	doc.extension_token_active = 0
	doc.save(ignore_permissions=True)

	return {"extension_token_active": 0}
