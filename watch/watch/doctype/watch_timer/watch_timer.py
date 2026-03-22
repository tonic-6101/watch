# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe.model.document import Document

from watch.utils.contexts import get_context_type_options


class WatchTimer(Document):
	def onload(self):
		"""Populate context_type Select options from installed apps."""
		self.set_onload("context_type_options", get_context_type_options())
