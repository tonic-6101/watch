# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

import frappe
from frappe import _


@frappe.whitelist()
def get_tags(
	search: str = None,
	category: str = None,
	include_archived: bool = False,
	include_stats: bool = False,
) -> list:
	"""Return tags, optionally filtered. Excludes archived by default."""
	filters = {}
	if category:
		filters["category"] = category
	if not include_archived:
		filters["is_archived"] = 0

	tags = frappe.get_all(
		"Watch Tag",
		filters=filters,
		fields=[
			"name", "tag_name", "category", "color",
			"default_entry_type", "is_archived",
			"monthly_hour_budget", "budget_warning_threshold",
		],
		order_by="tag_name asc",
	)

	if search:
		search_lower = search.lower()
		tags = [t for t in tags if search_lower in t.tag_name.lower()]

	if include_stats and tags:
		tag_names = [t.name for t in tags]
		placeholders = ", ".join(["%s"] * len(tag_names))

		counts = frappe.db.sql(
			f"""
			SELECT tag, COUNT(*) AS entry_count
			FROM `tabWatch Entry Tag`
			WHERE tag IN ({placeholders})
			GROUP BY tag
			""",
			tag_names,
			as_dict=True,
		)
		count_map = {r.tag: r.entry_count for r in counts}

		last_used_rows = frappe.db.sql(
			f"""
			SELECT tet.tag, MAX(te.date) AS last_used
			FROM `tabWatch Entry Tag` tet
			JOIN `tabWatch Entry` te ON te.name = tet.parent
			WHERE tet.tag IN ({placeholders})
			GROUP BY tet.tag
			""",
			tag_names,
			as_dict=True,
		)
		last_used_map = {r.tag: str(r.last_used) if r.last_used else None for r in last_used_rows}

		for t in tags:
			t["entry_count"] = count_map.get(t.name, 0)
			t["last_used"] = last_used_map.get(t.name)

	return tags


@frappe.whitelist()
def create_tag(
	tag_name: str,
	category: str = None,
	color: str = None,
	default_entry_type: str = None,
) -> dict:
	if frappe.db.exists("Watch Tag", tag_name):
		frappe.throw(_("Tag '{0}' already exists").format(tag_name))

	tag = frappe.new_doc("Watch Tag")
	tag.tag_name = tag_name
	if category:
		tag.category = category
	if color:
		tag.color = color
	if default_entry_type:
		tag.default_entry_type = default_entry_type
	tag.insert(ignore_permissions=True)
	return tag.as_dict()


@frappe.whitelist()
def update_tag(
	tag_name: str,
	category: str = None,
	color: str = None,
	default_entry_type: str = None,
	monthly_hour_budget: float = None,
	budget_warning_threshold: int = None,
) -> dict:
	tag = frappe.get_doc("Watch Tag", tag_name)
	if category is not None:
		tag.category = category
	if color is not None:
		tag.color = color
	if default_entry_type is not None:
		tag.default_entry_type = default_entry_type
	if monthly_hour_budget is not None:
		tag.monthly_hour_budget = monthly_hour_budget
	if budget_warning_threshold is not None:
		tag.budget_warning_threshold = budget_warning_threshold
	tag.save(ignore_permissions=True)
	return tag.as_dict()


@frappe.whitelist()
def rename_tag(tag_name: str, new_name: str) -> dict:
	"""Rename a tag and re-fetch denormalised fields on all child rows."""
	if not new_name or not new_name.strip():
		frappe.throw(_("New name cannot be empty"))
	new_name = new_name.strip()
	if new_name == tag_name:
		return frappe.get_doc("Watch Tag", tag_name).as_dict()
	if frappe.db.exists("Watch Tag", new_name):
		frappe.throw(_("Tag '{0}' already exists").format(new_name))

	# frappe.rename_doc handles the DB rename and updates Link fields
	frappe.rename_doc("Watch Tag", tag_name, new_name)

	# Re-fetch denormalised fields on child rows
	frappe.db.sql(
		"""
		UPDATE `tabWatch Entry Tag`
		SET tag_name = %s
		WHERE tag = %s
		""",
		(new_name, new_name),
	)

	return frappe.get_doc("Watch Tag", new_name).as_dict()


@frappe.whitelist()
def merge_tag(source: str, target: str) -> dict:
	"""
	Re-tag all entries: add target tag to entries that have source but not target,
	then archive source. Irreversible.
	"""
	if source == target:
		frappe.throw(_("Source and target must be different"))
	if not frappe.db.exists("Watch Tag", source):
		frappe.throw(_("Source tag '{0}' not found").format(source))
	if not frappe.db.exists("Watch Tag", target):
		frappe.throw(_("Target tag '{0}' not found").format(target))

	# Find entries that have source but not target
	source_entries = frappe.db.sql(
		"""
		SELECT DISTINCT parent FROM `tabWatch Entry Tag`
		WHERE tag = %s
		""",
		source,
		as_dict=True,
	)
	target_entries = {
		r[0]
		for r in (
			frappe.db.sql(
				"""
				SELECT DISTINCT parent FROM `tabWatch Entry Tag`
				WHERE tag = %s
				""",
				target,
				as_list=True,
			) or []
		)
	}

	target_tag = frappe.get_doc("Watch Tag", target)
	affected = 0

	for row in source_entries:
		entry_name = row.parent
		if entry_name not in target_entries:
			# Add target tag to this entry
			entry = frappe.get_doc("Watch Entry", entry_name)
			entry.append("tags", {
				"tag": target,
				"tag_name": target_tag.tag_name,
				"tag_color": target_tag.color,
				"tag_category": target_tag.category,
			})
			entry.save(ignore_permissions=True)
			affected += 1

	# Archive source
	frappe.db.set_value("Watch Tag", source, "is_archived", 1)

	return {"merged": source, "into": target, "entries_updated": affected}


@frappe.whitelist()
def archive_tag(tag_name: str, archive: bool = True) -> dict:
	"""Archive or unarchive a tag."""
	frappe.db.set_value("Watch Tag", tag_name, "is_archived", 1 if archive else 0)
	return frappe.get_doc("Watch Tag", tag_name).as_dict()


@frappe.whitelist()
def delete_tag(tag_name: str) -> dict:
	in_use = frappe.db.count("Watch Entry Tag", {"tag": tag_name})
	if in_use:
		frappe.throw(
			_("Tag '{0}' is used in {1} entries. Archive it instead of deleting.").format(
				tag_name, in_use
			)
		)
	frappe.delete_doc("Watch Tag", tag_name, ignore_permissions=True)
	return {"deleted": tag_name}


@frappe.whitelist()
def get_tag_stats(tag_name: str) -> dict:
	"""Return entry count and last-used date for a single tag."""
	entry_count = frappe.db.count("Watch Entry Tag", {"tag": tag_name})
	last_used = frappe.db.sql(
		"""
		SELECT MAX(te.date)
		FROM `tabWatch Entry Tag` tet
		JOIN `tabWatch Entry` te ON te.name = tet.parent
		WHERE tet.tag = %s
		""",
		tag_name,
	)
	return {
		"tag_name": tag_name,
		"entry_count": entry_count,
		"last_used": str(last_used[0][0]) if last_used and last_used[0][0] else None,
	}


@frappe.whitelist()
def search_tags(query: str = None) -> list:
	"""Autocomplete search — returns tag_name + metadata for chip input."""
	return get_tags(search=query)


# ── Budget ────────────────────────────────────────────────────────────────────


def _budget_status(used: float, budget: float, threshold_pct: int) -> dict:
	status = "none"
	if budget > 0:
		pct = (used / budget) * 100
		if pct >= 100:
			status = "exceeded"
		elif pct >= threshold_pct:
			status = "approaching"
	return {
		"used":          round(used, 4),
		"budget":        budget,
		"pct":           round(used / budget * 100, 1) if budget > 0 else None,
		"status":        status,
		"threshold_pct": threshold_pct,
	}


@frappe.whitelist()
def get_budget_usage(tag_name: str, month: str = None) -> dict:
	"""
	Return budget usage for a tag in a given month (YYYY-MM, default: current).
	Budget is site-wide — all users' hours count.
	"""
	if not month:
		month = frappe.utils.today()[:7]

	month_start = f"{month}-01"
	month_end   = str(frappe.utils.get_last_day(month_start))

	result = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(e.duration_hours), 0) AS total_hours
		FROM `tabWatch Entry` e
		JOIN `tabWatch Entry Tag` et ON et.parent = e.name
		WHERE et.tag = %(tag)s
		  AND e.date BETWEEN %(start)s AND %(end)s
		  AND e.is_running = 0
		""",
		{"tag": tag_name, "start": month_start, "end": month_end},
		as_dict=True,
	)

	used = float(result[0].total_hours) if result else 0.0

	if not frappe.db.exists("Watch Tag", tag_name):
		return {"status": "none", "used": round(used, 2), "budget": 0, "pct": 0}

	tag      = frappe.get_cached_doc("Watch Tag", tag_name)
	budget   = float(tag.monthly_hour_budget or 0)
	settings = frappe.get_single("Watch Settings")
	threshold_pct = int(tag.budget_warning_threshold or settings.budget_warning_threshold or 80)

	return _budget_status(used, budget, threshold_pct)


@frappe.whitelist()
def get_all_budgets(month: str = None) -> dict:
	"""
	Return budget status for all tags that have monthly_hour_budget > 0.
	Keyed by tag name (Watch Tag.name). Used by the tag management page.
	"""
	if not month:
		month = frappe.utils.today()[:7]

	month_start = f"{month}-01"
	month_end   = str(frappe.utils.get_last_day(month_start))

	budget_tags = frappe.get_all(
		"Watch Tag",
		filters={"monthly_hour_budget": [">", 0]},
		fields=["name", "monthly_hour_budget", "budget_warning_threshold"],
	)
	if not budget_tags:
		return {}

	tag_names    = [t.name for t in budget_tags]
	placeholders = ", ".join(["%s"] * len(tag_names))

	usage_rows = frappe.db.sql(
		f"""
		SELECT et.tag, COALESCE(SUM(e.duration_hours), 0) AS total_hours
		FROM `tabWatch Entry` e
		JOIN `tabWatch Entry Tag` et ON et.parent = e.name
		WHERE et.tag IN ({placeholders})
		  AND e.date BETWEEN %s AND %s
		  AND e.is_running = 0
		GROUP BY et.tag
		""",
		tag_names + [month_start, month_end],
		as_dict=True,
	)
	usage_map = {r.tag: float(r.total_hours) for r in usage_rows}

	settings      = frappe.get_single("Watch Settings")
	site_threshold = int(settings.budget_warning_threshold or 80)

	result = {}
	for t in budget_tags:
		used          = usage_map.get(t.name, 0.0)
		budget        = float(t.monthly_hour_budget or 0)
		threshold_pct = int(t.budget_warning_threshold or site_threshold)
		result[t.name] = _budget_status(used, budget, threshold_pct)

	return result


# ── Proactive budget alerts ────────────────────────────────────────────────


def _check_budget_alerts(entry):
	"""Check if any tag on this entry crossed its budget threshold.

	Creates a Dock Notification when a threshold is crossed.
	Deduplicates: one notification per tag+type+user+month.
	Soft dependency on Dock — silently skips if Dock is not installed.
	"""
	if "dock" not in frappe.get_installed_apps():
		return

	tag_rows = entry.tags if hasattr(entry, "tags") else []
	if not tag_rows:
		return

	entry_date = str(entry.date)
	month = entry_date[:7]
	month_start = f"{month}-01"
	month_end = str(frappe.utils.get_last_day(month_start))

	settings = frappe.get_single("Watch Settings")
	site_threshold = int(settings.budget_warning_threshold or 80)

	for tag_row in tag_rows:
		tag_name = tag_row.tag
		if not frappe.db.exists("Watch Tag", tag_name):
			continue

		tag = frappe.get_cached_doc("Watch Tag", tag_name)
		budget = float(tag.monthly_hour_budget or 0)
		if budget <= 0:
			continue

		threshold_pct = int(tag.budget_warning_threshold or site_threshold)

		result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(e.duration_hours), 0) AS total_hours
			FROM `tabWatch Entry` e
			JOIN `tabWatch Entry Tag` et ON et.parent = e.name
			WHERE et.tag = %(tag)s
			  AND e.date BETWEEN %(start)s AND %(end)s
			  AND e.is_running = 0
			""",
			{"tag": tag_name, "start": month_start, "end": month_end},
			as_dict=True,
		)

		used = float(result[0].total_hours) if result else 0.0
		pct = (used / budget) * 100

		if pct >= 100:
			notif_type = "budget_exceeded"
			title = _("{0}: budget exceeded ({1}%)").format(tag_name, int(pct))
		elif pct >= threshold_pct:
			notif_type = "budget_warning"
			title = _("{0}: {1}% of budget used").format(tag_name, int(pct))
		else:
			continue

		# Deduplicate: skip if same-type notification exists for this tag+user this month
		existing = frappe.db.get_all(
			"Dock Notification",
			filters={
				"for_user": entry.user,
				"from_app": "watch",
				"notification_type": notif_type,
				"reference_doctype": "Watch Tag",
				"reference_name": tag_name,
				"creation": [">=", month_start],
			},
			limit=1,
		)
		if existing:
			continue

		try:
			frappe.call(
				"dock.api.notifications.publish",
				for_user=entry.user,
				from_app="watch",
				notification_type=notif_type,
				title=title,
				message=_("{0}: {1}h of {2}h budget used this month").format(
					tag_name, round(used, 1), round(budget, 1)
				),
				reference_doctype="Watch Tag",
				reference_name=tag_name,
				action_url="/watch/tags",
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Watch budget alert")
