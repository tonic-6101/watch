# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

from datetime import datetime

import frappe
from frappe import _


def _fire_timer_stopped(entry):
	"""Notify Slack and fire watch_event_hooks after a timer stop.  Never raises."""
	try:
		from watch.api.integrations import fire_watch_event, notify_slack
		entry_data = entry.as_dict()
		notify_slack(entry_data)
		fire_watch_event("timer_stopped", {"entry": entry_data})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch timer_stopped integrations")


def _get_or_create_timer(user: str):
	if frappe.db.exists("FT Timer", user):
		return frappe.get_doc("FT Timer", user)
	timer = frappe.new_doc("FT Timer")
	timer.user = user
	timer.state = "stopped"
	timer.accumulated_seconds = 0
	timer.insert(ignore_permissions=True)
	return timer


def _elapsed_seconds(timer) -> int:
	"""Total elapsed seconds including accumulated (for running/paused state)."""
	if timer.state == "running" and timer.started_at:
		started = timer.started_at
		if isinstance(started, str):
			started = datetime.fromisoformat(started)
		delta = datetime.now() - started
		return int(timer.accumulated_seconds + delta.total_seconds())
	return int(timer.accumulated_seconds)


def _publish(user: str, payload: dict):
	frappe.publish_realtime("dock_timer_update", payload, user=user)


@frappe.whitelist()
def start_timer(
	description: str = None,
	tags: list = None,
	entry_type: str = "billable",
) -> dict:
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state == "running":
		frappe.throw(_("Timer is already running"))

	if tags and isinstance(tags, str):
		import json
		tags = json.loads(tags)

	# Create the time entry
	entry = frappe.new_doc("FT Time Entry")
	entry.date = frappe.utils.today()
	entry.user = user
	entry.description = description
	entry.entry_type = entry_type or "billable"
	entry.is_running = 1
	entry.timer_started_at = frappe.utils.now_datetime()

	if tags:
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})

	entry.insert(ignore_permissions=True)

	now = frappe.utils.now_datetime()
	timer.state = "running"
	timer.started_at = now
	timer.accumulated_seconds = 0
	timer.active_entry = entry.name
	timer.description = description
	timer.save(ignore_permissions=True)

	payload = {"state": "running", "entry": entry.name, "description": description}
	_publish(user, payload)

	return {"timer": timer.as_dict(), "entry": entry.name}


@frappe.whitelist()
def stop_timer(notes: str = None) -> dict:
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state == "stopped":
		frappe.throw(_("No timer is running"))

	now = frappe.utils.now_datetime()
	started = timer.started_at
	if isinstance(started, str):
		started = datetime.fromisoformat(started)

	if timer.state == "running":
		elapsed = timer.accumulated_seconds + (now - started).total_seconds()
	else:
		elapsed = timer.accumulated_seconds

	entry = frappe.get_doc("FT Time Entry", timer.active_entry)
	entry.end_time = now.strftime("%H:%M:%S")
	entry.duration_hours = round(elapsed / 3600, 4)
	entry.is_running = 0

	if notes:
		entry.description = (
			f"{entry.description}\n{notes}".strip() if entry.description else notes
		)

	entry.save(ignore_permissions=True)

	timer.state = "stopped"
	timer.accumulated_seconds = 0
	timer.active_entry = None
	timer.description = None
	timer.started_at = None
	timer.paused_at = None
	timer.save(ignore_permissions=True)

	_publish(user, {"state": "stopped", "entry": entry.name})

	_fire_timer_stopped(entry)

	return {"entry": entry.as_dict()}


@frappe.whitelist()
def pause_timer() -> dict:
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state != "running":
		frappe.throw(_("Timer is not running"))

	now = frappe.utils.now_datetime()
	started = timer.started_at
	if isinstance(started, str):
		started = datetime.fromisoformat(started)

	timer.accumulated_seconds = int(
		timer.accumulated_seconds + (now - started).total_seconds()
	)
	timer.state = "paused"
	timer.paused_at = now
	timer.started_at = None
	timer.save(ignore_permissions=True)

	_publish(user, {"state": "paused", "accumulated_seconds": timer.accumulated_seconds})

	return {"accumulated_seconds": timer.accumulated_seconds}


@frappe.whitelist()
def resume_timer() -> dict:
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state != "paused":
		frappe.throw(_("Timer is not paused"))

	now = frappe.utils.now_datetime()
	timer.state = "running"
	timer.started_at = now
	timer.paused_at = None
	timer.save(ignore_permissions=True)

	_publish(user, {"state": "running", "accumulated_seconds": timer.accumulated_seconds})

	return {"state": "running", "accumulated_seconds": timer.accumulated_seconds}


@frappe.whitelist()
def get_timer_state() -> dict:
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	elapsed = _elapsed_seconds(timer) if timer.state != "stopped" else 0

	active_entry_date = None
	if timer.active_entry:
		active_entry_date = frappe.db.get_value("FT Time Entry", timer.active_entry, "date")
		if active_entry_date:
			active_entry_date = str(active_entry_date)

	return {
		"state": timer.state,
		"elapsed_seconds": elapsed,
		"accumulated_seconds": int(timer.accumulated_seconds),
		"description": timer.description,
		"active_entry": timer.active_entry,
		"active_entry_date": active_entry_date,
		"started_at": str(timer.started_at) if timer.started_at else None,
		# Focus mode fields
		"focus_mode": bool(timer.focus_mode),
		"focus_phase": timer.focus_phase or "work",
		"focus_session_number": int(timer.focus_session_number or 1),
		"focus_total_sessions": int(timer.focus_total_sessions or 4),
		"focus_work_minutes": int(timer.focus_work_minutes or 25),
		"focus_break_minutes": int(timer.focus_break_minutes or 5),
		"focus_description": timer.focus_description,
	}


@frappe.whitelist()
def stop_timer_at(stop_at: str, notes: str = None) -> dict:
	"""Stop the timer retroactively at a given datetime.

	Used by the idle prompt when the user chooses "Stop at {time}".
	The entry end_time is set to stop_at; elapsed time is recalculated.
	"""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state == "stopped":
		frappe.throw(_("No timer is running"))

	stop_dt = frappe.utils.get_datetime(stop_at)
	entry = frappe.get_doc("FT Time Entry", timer.active_entry)

	started = entry.timer_started_at
	if isinstance(started, str):
		started = datetime.fromisoformat(started)

	elapsed = max((stop_dt - started).total_seconds() + timer.accumulated_seconds, 0)

	entry.end_time = stop_dt.strftime("%H:%M:%S")
	entry.duration_hours = round(elapsed / 3600, 4)
	entry.is_running = 0

	if notes:
		entry.description = (
			f"{entry.description}\n{notes}".strip() if entry.description else notes
		)

	entry.save(ignore_permissions=True)

	timer.state = "stopped"
	timer.accumulated_seconds = 0
	timer.active_entry = None
	timer.description = None
	timer.started_at = None
	timer.paused_at = None
	timer.save(ignore_permissions=True)

	_publish(user, {"state": "stopped", "entry": entry.name})

	_fire_timer_stopped(entry)

	return {"entry": entry.as_dict()}


@frappe.whitelist()
def update_timer(
	description: str = None,
	tags: list = None,
	entry_type: str = None,
) -> dict:
	"""Update the running/paused timer's entry context without stopping."""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state == "stopped":
		frappe.throw(_("No active timer to update"))

	if tags and isinstance(tags, str):
		import json
		tags = json.loads(tags)

	entry = frappe.get_doc("FT Time Entry", timer.active_entry)

	if description is not None:
		entry.description = description
		timer.description = description

	if entry_type:
		entry.entry_type = entry_type

	if tags is not None:
		entry.set("tags", [])
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})

	entry.save(ignore_permissions=True)
	timer.save(ignore_permissions=True)

	_publish(user, {
		"state": timer.state,
		"entry": entry.name,
		"description": entry.description,
	})

	return {"entry": entry.as_dict()}


# ── Focus mode (Pomodoro) ────────────────────────────────────────────────


def _reset_focus_timer(timer) -> None:
	timer.state = "stopped"
	timer.accumulated_seconds = 0
	timer.active_entry = None
	timer.description = None
	timer.started_at = None
	timer.paused_at = None
	timer.focus_mode = 0
	timer.focus_phase = "work"
	timer.focus_session_number = 1
	timer.focus_description = None
	timer.save(ignore_permissions=True)


def _create_focus_entry(user: str, timer, entry_type: str, tags: list):
	now = frappe.utils.now_datetime()
	entry = frappe.new_doc("FT Time Entry")
	entry.date = frappe.utils.today()
	entry.user = user
	entry.description = timer.focus_description
	entry.entry_type = entry_type or "billable"
	entry.is_running = 1
	entry.timer_started_at = now
	if tags:
		for tag_name in tags:
			entry.append("tags", {"tag": tag_name})
	entry.insert(ignore_permissions=True)
	return entry, now


@frappe.whitelist()
def start_focus(
	description: str = None,
	tags: list = None,
	entry_type: str = "billable",
	sessions: int = 4,
	work_minutes: int = 25,
	break_minutes: int = 5,
) -> dict:
	"""Initialise a focus (Pomodoro) run and start the first work session."""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if timer.state != "stopped":
		frappe.throw(_("Timer is already running"))

	if tags and isinstance(tags, str):
		import json
		tags = json.loads(tags)

	# Persist focus config on timer
	timer.focus_mode = 1
	timer.focus_phase = "work"
	timer.focus_session_number = 1
	timer.focus_total_sessions = int(sessions)
	timer.focus_work_minutes = int(work_minutes)
	timer.focus_break_minutes = int(break_minutes)
	timer.focus_description = description
	timer.description = description

	# Create entry for session 1
	entry, now = _create_focus_entry(user, timer, entry_type, tags or [])

	timer.state = "running"
	timer.started_at = now
	timer.accumulated_seconds = 0
	timer.active_entry = entry.name
	timer.save(ignore_permissions=True)

	_publish(user, {
		"state": "running",
		"focus_mode": True,
		"focus_phase": "work",
		"focus_session_number": 1,
		"focus_total_sessions": int(sessions),
		"focus_work_minutes": int(work_minutes),
		"focus_break_minutes": int(break_minutes),
		"entry": entry.name,
	})

	return {"timer": timer.as_dict(), "entry": entry.name}


@frappe.whitelist()
def end_focus_session() -> dict:
	"""Finalise the current work-session entry and advance to break (or complete)."""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if not timer.focus_mode:
		frappe.throw(_("No focus session is running"))

	now = frappe.utils.now_datetime()
	started = timer.started_at
	if isinstance(started, str):
		started = datetime.fromisoformat(started)

	if timer.state == "running" and started:
		elapsed = timer.accumulated_seconds + (now - started).total_seconds()
	else:
		elapsed = timer.accumulated_seconds

	# Finalise the active entry
	entry = None
	if timer.active_entry:
		entry = frappe.get_doc("FT Time Entry", timer.active_entry)
		entry.end_time = now.strftime("%H:%M:%S")
		entry.duration_hours = round(elapsed / 3600, 4)
		entry.is_running = 0
		entry.save(ignore_permissions=True)
		_fire_timer_stopped(entry)

	session_num = int(timer.focus_session_number or 1)
	total = int(timer.focus_total_sessions or 4)
	completed = session_num >= total

	if completed:
		_reset_focus_timer(timer)
		_publish(user, {"state": "stopped", "focus_mode": False, "focus_completed": True})
		return {"completed": True}

	# Move to break
	timer.state = "stopped"
	timer.accumulated_seconds = 0
	timer.active_entry = None
	timer.started_at = None
	timer.paused_at = None
	timer.focus_phase = "break"
	timer.save(ignore_permissions=True)

	_publish(user, {
		"state": "stopped",
		"focus_mode": True,
		"focus_phase": "break",
		"focus_session_number": session_num,
		"focus_total_sessions": total,
		"focus_break_minutes": int(timer.focus_break_minutes or 5),
	})

	return {
		"completed": False,
		"focus_phase": "break",
		"focus_session_number": session_num,
		"focus_break_minutes": int(timer.focus_break_minutes or 5),
	}


@frappe.whitelist()
def skip_break(entry_type: str = "billable", tags: list = None) -> dict:
	"""Skip the current break and immediately start the next work session."""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if not timer.focus_mode or timer.focus_phase != "break":
		frappe.throw(_("No break is active"))

	if tags and isinstance(tags, str):
		import json
		tags = json.loads(tags)

	next_session = int(timer.focus_session_number or 1) + 1
	timer.focus_session_number = next_session
	timer.focus_phase = "work"

	entry, now = _create_focus_entry(user, timer, entry_type or "billable", tags or [])

	timer.state = "running"
	timer.started_at = now
	timer.accumulated_seconds = 0
	timer.active_entry = entry.name
	timer.save(ignore_permissions=True)

	_publish(user, {
		"state": "running",
		"focus_mode": True,
		"focus_phase": "work",
		"focus_session_number": next_session,
		"focus_total_sessions": int(timer.focus_total_sessions or 4),
		"entry": entry.name,
	})

	return {"focus_session_number": next_session, "entry": entry.name}


@frappe.whitelist()
def end_focus() -> dict:
	"""Abort the entire focus run, saving any partial elapsed time."""
	user = frappe.session.user
	timer = _get_or_create_timer(user)

	if not timer.focus_mode:
		frappe.throw(_("No focus session is running"))

	now = frappe.utils.now_datetime()
	started = timer.started_at
	if isinstance(started, str):
		started = datetime.fromisoformat(started)

	# Save partial entry if there is one running with non-trivial time
	if timer.active_entry and timer.state == "running" and started:
		elapsed = timer.accumulated_seconds + (now - started).total_seconds()
		if elapsed > 30:
			entry = frappe.get_doc("FT Time Entry", timer.active_entry)
			entry.end_time = now.strftime("%H:%M:%S")
			entry.duration_hours = round(elapsed / 3600, 4)
			entry.is_running = 0
			entry.save(ignore_permissions=True)
			_fire_timer_stopped(entry)
		else:
			frappe.delete_doc("FT Time Entry", timer.active_entry, ignore_permissions=True)
	elif timer.active_entry:
		frappe.delete_doc("FT Time Entry", timer.active_entry, ignore_permissions=True)

	_reset_focus_timer(timer)
	_publish(user, {"state": "stopped", "focus_mode": False})

	return {"stopped": True}
