# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _
from frappe.model.document import Document


class FTTimeEntry(Document):
	def validate(self):
		self._check_lock()
		self._calculate_duration()
		self._calculate_entry_amount()

	def after_insert(self):
		self._fire_integration_event("entry_created")

	def on_update(self):
		self._trigger_erpnext_sync()
		self._fire_integration_event("entry_updated")

	def _trigger_erpnext_sync(self):
		"""Enqueue ERPNext sync when sync_mode = on_save. Never blocks the save."""
		if self.is_running:
			return
		try:
			settings = frappe.get_single("FT Settings")
			if settings.enable_erpnext_bridge and settings.sync_mode == "on_save":
				frappe.enqueue(
					"watch.api.erpnext_bridge.sync_entry",
					entry_name=self.name,
					queue="short",
					now=frappe.flags.in_test,
				)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Watch ERPNext Bridge on_save")

	def _check_lock(self):
		"""Block saves on entries older than the configured lock threshold."""
		if self.is_new() or self.is_running:
			return
		try:
			settings = frappe.get_single("FT Settings")
		except Exception:
			return
		days = settings.lock_entries_older_than or 0
		if not days:
			return
		cutoff = frappe.utils.add_days(frappe.utils.today(), -days)
		if str(self.date) < str(cutoff):
			frappe.throw(
				_("Entries older than {0} days are locked. Contact your administrator.").format(days)
			)

	def _calculate_duration(self):
		if self.start_time and self.end_time and not self.is_running:
			from datetime import datetime, date
			fmt = "%H:%M:%S"
			start = datetime.strptime(str(self.start_time), fmt)
			end = datetime.strptime(str(self.end_time), fmt)
			delta = end - start
			if delta.total_seconds() > 0:
				self.duration_hours = round(delta.total_seconds() / 3600, 4)

	def _fire_integration_event(self, event: str):
		"""Fire watch_event_hooks and post comments to Linear/GitHub.  Never raises."""
		if self.is_running:
			return
		try:
			from watch.api.integrations import (
				fire_watch_event,
				post_linear_comment,
				post_github_comment,
			)
			fire_watch_event(event, {"entry": self.as_dict()})
			if event in ("entry_created", "entry_updated"):
				post_linear_comment(self.name)
				post_github_comment(self.name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Watch integration event: {event}")

	def _calculate_entry_amount(self):
		if self.entry_type == "billable" and self.entry_rate and self.duration_hours:
			from watch.utils.rounding import get_billing_duration
			billed_hours = get_billing_duration(self)
			self.entry_amount = round(billed_hours * self.entry_rate, 2)
		else:
			self.entry_amount = 0
