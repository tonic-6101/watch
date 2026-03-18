# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""Tests for watch.api.timer — timer lifecycle and state transitions."""

from datetime import datetime, timedelta
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from watch.api.timer import (
	get_timer_state,
	pause_timer,
	resume_timer,
	start_timer,
	stop_timer,
	stop_timer_at,
	update_timer,
)
from watch.tests.test_helpers import cleanup_timer, ensure_ft_settings


class TestTimerAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_ft_settings()

	def setUp(self):
		frappe.set_user("Administrator")
		cleanup_timer()

	# ── start_timer ──────────────────────────────────────────────────────

	def test_start_creates_entry_and_timer(self):
		result = start_timer(description="Working on tests")

		self.assertIn("timer", result)
		self.assertIn("entry", result)

		timer = result["timer"]
		self.assertEqual(timer["state"], "running")
		self.assertIsNotNone(timer["active_entry"])

		entry = frappe.get_doc("FT Time Entry", result["entry"])
		self.assertEqual(entry.is_running, 1)
		self.assertEqual(entry.description, "Working on tests")
		self.assertEqual(entry.entry_type, "billable")
		self.assertIsNotNone(entry.timer_started_at)

	def test_start_with_tags(self):
		result = start_timer(description="Tagged work", tags=["client-a", "dev"])
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		tag_names = [row.tag for row in entry.tags]
		self.assertIn("client-a", tag_names)
		self.assertIn("dev", tag_names)

	def test_start_with_entry_type(self):
		result = start_timer(entry_type="non-billable")
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		self.assertEqual(entry.entry_type, "non-billable")

	def test_start_throws_if_already_running(self):
		start_timer()
		with self.assertRaises(frappe.exceptions.ValidationError):
			start_timer()

	# ── stop_timer ───────────────────────────────────────────────────────

	def test_stop_calculates_duration(self):
		t0 = datetime(2026, 3, 13, 9, 0, 0)
		t1 = datetime(2026, 3, 13, 10, 30, 0)

		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				result = start_timer(description="Timed work")

		with patch("frappe.utils.now_datetime", return_value=t1):
			result = stop_timer()

		entry = result["entry"]
		self.assertEqual(entry["is_running"], 0)
		self.assertIsNotNone(entry["end_time"])
		# 1.5 hours elapsed
		self.assertAlmostEqual(entry["duration_hours"], 1.5, places=2)

	def test_stop_appends_notes(self):
		start_timer(description="Initial")
		result = stop_timer(notes="wrap-up note")
		self.assertIn("wrap-up note", result["entry"]["description"])

	def test_stop_resets_timer_state(self):
		start_timer()
		stop_timer()
		timer = frappe.get_doc("FT Timer", "Administrator")
		self.assertEqual(timer.state, "stopped")
		self.assertIsNone(timer.active_entry)
		self.assertEqual(timer.accumulated_seconds, 0)

	def test_stop_throws_if_not_running(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			stop_timer()

	# ── pause_timer ──────────────────────────────────────────────────────

	def test_pause_accumulates_seconds(self):
		t0 = datetime(2026, 3, 13, 9, 0, 0)
		t1 = datetime(2026, 3, 13, 9, 10, 0)

		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				start_timer()

		with patch("frappe.utils.now_datetime", return_value=t1):
			result = pause_timer()

		self.assertEqual(result["accumulated_seconds"], 600)  # 10 minutes
		timer = frappe.get_doc("FT Timer", "Administrator")
		self.assertEqual(timer.state, "paused")
		self.assertIsNone(timer.started_at)

	def test_pause_throws_if_not_running(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			pause_timer()

	def test_pause_throws_if_paused(self):
		start_timer()
		pause_timer()
		with self.assertRaises(frappe.exceptions.ValidationError):
			pause_timer()

	# ── resume_timer ─────────────────────────────────────────────────────

	def test_resume_from_paused(self):
		start_timer()
		pause_timer()
		result = resume_timer()
		self.assertEqual(result["state"], "running")
		timer = frappe.get_doc("FT Timer", "Administrator")
		self.assertEqual(timer.state, "running")
		self.assertIsNotNone(timer.started_at)

	def test_resume_throws_if_not_paused(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			resume_timer()

	def test_resume_throws_if_running(self):
		start_timer()
		with self.assertRaises(frappe.exceptions.ValidationError):
			resume_timer()

	# ── pause → resume → stop preserves accumulated ─────────────────────

	def test_pause_resume_stop_duration(self):
		"""Total duration should include time before pause and time after resume."""
		t0 = datetime(2026, 3, 13, 9, 0, 0)
		t1 = datetime(2026, 3, 13, 9, 20, 0)   # pause after 20 min
		t2 = datetime(2026, 3, 13, 9, 30, 0)   # resume (10 min paused, not counted)
		t3 = datetime(2026, 3, 13, 9, 40, 0)   # stop after 10 more min

		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				result = start_timer()

		with patch("frappe.utils.now_datetime", return_value=t1):
			pause_timer()

		with patch("frappe.utils.now_datetime", return_value=t2):
			resume_timer()

		with patch("frappe.utils.now_datetime", return_value=t3):
			result = stop_timer()

		# 20 min + 10 min = 30 min = 0.5 hours
		self.assertAlmostEqual(result["entry"]["duration_hours"], 0.5, places=2)

	# ── get_timer_state ──────────────────────────────────────────────────

	def test_get_state_stopped(self):
		state = get_timer_state()
		self.assertEqual(state["state"], "stopped")
		self.assertEqual(state["elapsed_seconds"], 0)
		self.assertIsNone(state["active_entry"])

	def test_get_state_running(self):
		t0 = datetime(2026, 3, 13, 14, 0, 0)
		t1 = datetime(2026, 3, 13, 14, 5, 0)

		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				start_timer(description="test state")

		with patch("frappe.utils.now_datetime", return_value=t1):
			state = get_timer_state()

		self.assertEqual(state["state"], "running")
		self.assertEqual(state["elapsed_seconds"], 300)
		self.assertEqual(state["description"], "test state")
		self.assertIsNotNone(state["active_entry"])

	def test_get_state_includes_focus_fields(self):
		state = get_timer_state()
		self.assertIn("focus_mode", state)
		self.assertIn("focus_phase", state)
		self.assertIn("focus_session_number", state)

	# ── update_timer ─────────────────────────────────────────────────────

	def test_update_description(self):
		result = start_timer(description="original")
		update_timer(description="updated")
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		self.assertEqual(entry.description, "updated")
		timer = frappe.get_doc("FT Timer", "Administrator")
		self.assertEqual(timer.description, "updated")

	def test_update_tags(self):
		result = start_timer()
		update_timer(tags=["new-tag"])
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		tag_names = [row.tag for row in entry.tags]
		self.assertEqual(tag_names, ["new-tag"])

	def test_update_entry_type(self):
		result = start_timer(entry_type="billable")
		update_timer(entry_type="non-billable")
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		self.assertEqual(entry.entry_type, "non-billable")

	def test_update_throws_if_stopped(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			update_timer(description="nope")

	def test_update_works_when_paused(self):
		result = start_timer(description="before pause")
		pause_timer()
		update_timer(description="while paused")
		entry = frappe.get_doc("FT Time Entry", result["entry"])
		self.assertEqual(entry.description, "while paused")

	# ── stop_timer_at ────────────────────────────────────────────────────

	def test_stop_at_retroactive(self):
		t0 = datetime(2026, 3, 13, 9, 0, 0)
		stop_at = datetime(2026, 3, 13, 9, 45, 0)

		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				start_timer(description="retroactive stop")

		result = stop_timer_at(stop_at=stop_at.isoformat())
		entry = result["entry"]
		self.assertEqual(entry["is_running"], 0)
		# 45 min = 0.75 hours
		self.assertAlmostEqual(entry["duration_hours"], 0.75, places=2)
		self.assertEqual(entry["end_time"], "09:45:00")

	def test_stop_at_throws_if_stopped(self):
		with self.assertRaises(frappe.exceptions.ValidationError):
			stop_timer_at(stop_at="2026-03-13 10:00:00")

	def test_stop_at_with_notes(self):
		t0 = datetime(2026, 3, 13, 9, 0, 0)
		with patch("frappe.utils.now_datetime", return_value=t0):
			with patch("frappe.utils.today", return_value="2026-03-13"):
				start_timer(description="work")

		result = stop_timer_at(
			stop_at="2026-03-13 09:30:00",
			notes="stopped retroactively",
		)
		self.assertIn("stopped retroactively", result["entry"]["description"])
