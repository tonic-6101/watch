# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2024-2026 Tonic

"""
Integrations: Slack, Linear, GitHub.

All outbound integration logic lives here.  Built-in integrations are driven
by Watch Settings fields; the ``watch_event_hooks`` contract is for third-party
extensibility.
"""

import requests

import frappe
from frappe import _


# ── Helpers ──────────────────────────────────────────────────────────────


def _format_duration(hours: float) -> str:
	"""Format hours as '1h 24m'."""
	if not hours:
		return "0m"
	h = int(hours)
	m = int(round((hours - h) * 60))
	if h > 0 and m > 0:
		return f"{h}h {m}m"
	if h > 0:
		return f"{h}h"
	return f"{m}m"


def _get_entry_tags(entry) -> list[str]:
	"""Return tag names for an entry (works with doc or dict)."""
	if hasattr(entry, "tags"):
		return [t.tag_name or t.tag for t in entry.tags]
	return entry.get("tag_names", [])


# ── Event dispatcher ─────────────────────────────────────────────────────


def fire_watch_event(event: str, payload: dict):
	"""Call all registered handlers for a watch event.

	Handlers run synchronously.  Heavy work should be enqueued by the handler.
	"""
	installed = frappe.get_installed_apps()
	handlers = frappe.get_hooks("watch_event_hooks") or []
	for h in handlers:
		if not isinstance(h, dict):
			continue
		if h.get("app") not in installed:
			continue
		if h.get("event") != event:
			continue
		try:
			frappe.call(h["endpoint"], **payload)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"watch_event_hooks: {h.get('endpoint')}",
			)


# ── Slack ────────────────────────────────────────────────────────────────


def build_slack_message(entry: dict) -> str:
	"""Build the Slack notification message from an entry dict."""
	duration_str = _format_duration(entry.get("duration_hours") or 0)
	description = entry.get("description") or _("(no description)")

	tag_parts = []
	for tag in _get_entry_tags(entry):
		tag_parts.append(f"[{tag}]")
	entry_type = entry.get("entry_type")
	if entry_type and entry_type != "non-billable":
		tag_parts.append(f"[{_(entry_type.title())}]")
	tag_str = " \u00b7 " + " ".join(tag_parts) if tag_parts else ""

	template = (
		frappe.db.get_single_value("Watch Settings", "slack_message_template")
		or "\u23f1 {description} \u2014 {duration} logged{tag_part}"
	)

	return template.format(
		description=description,
		duration=duration_str,
		tag_part=tag_str,
		user=frappe.session.user,
	)


def notify_slack(entry: dict):
	"""Post a message to the configured Slack webhook.  Failures are silent."""
	try:
		settings = frappe.get_single("Watch Settings")
		if not settings.slack_webhook_url or not settings.slack_notify_on_stop:
			return

		message = build_slack_message(entry)
		requests.post(
			settings.slack_webhook_url,
			json={"text": message},
			timeout=5,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch Slack notification failed")


@frappe.whitelist()
def test_slack() -> dict:
	"""Send a test message to the configured Slack webhook."""
	if not "System Manager" in frappe.get_roles():
		frappe.throw(_("Only System Manager can test integrations"), frappe.PermissionError)

	url = frappe.db.get_single_value("Watch Settings", "slack_webhook_url")
	if not url:
		frappe.throw(_("No Slack webhook URL configured"))

	resp = requests.post(url, json={"text": "\u2713 Watch connected successfully"}, timeout=5)
	resp.raise_for_status()
	return {"status": "ok"}


# ── Linear ───────────────────────────────────────────────────────────────


def _linear_request(api_key: str, query: str, variables: dict = None) -> dict:
	"""Execute a GraphQL request against the Linear API."""
	payload = {"query": query}
	if variables:
		payload["variables"] = variables
	resp = requests.post(
		"https://api.linear.app/graphql",
		headers={"Authorization": api_key, "Content-Type": "application/json"},
		json=payload,
		timeout=5,
	)
	resp.raise_for_status()
	return resp.json()


@frappe.whitelist()
def test_linear() -> dict:
	"""Validate the Linear API key; returns workspace name."""
	if not "System Manager" in frappe.get_roles():
		frappe.throw(_("Only System Manager can test integrations"), frappe.PermissionError)

	api_key = frappe.db.get_single_value("Watch Settings", "linear_api_key")
	if not api_key:
		frappe.throw(_("No Linear API key configured"))

	data = _linear_request(api_key, "query { viewer { name } organization { name } }")
	org = data.get("data", {}).get("organization", {}).get("name", "")
	return {"status": "ok", "workspace": org}


@frappe.whitelist()
def search_linear_issues(query: str) -> list:
	"""Search Linear issues by identifier or title."""
	api_key = frappe.db.get_single_value("Watch Settings", "linear_api_key")
	if not api_key or len(query) < 2:
		return []

	gql = """
	query($filter: IssueFilter) {
		issues(filter: $filter, first: 10) {
			nodes { identifier title url }
		}
	}
	"""
	variables = {
		"filter": {
			"or": [
				{"identifier": {"containsIgnoreCase": query}},
				{"title": {"containsIgnoreCase": query}},
			]
		}
	}

	try:
		data = _linear_request(api_key, gql, variables)
		nodes = data.get("data", {}).get("issues", {}).get("nodes", [])
		return [
			{
				"value": n["identifier"],
				"label": f"{n['identifier']}: {n['title']}",
				"url": n["url"],
			}
			for n in nodes
		]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch Linear search failed")
		return []


def _resolve_linear_issue_id(identifier: str, api_key: str) -> str | None:
	"""Resolve a Linear issue identifier (e.g. ENG-123) to its internal ID."""
	gql = """
	query($filter: IssueFilter) {
		issues(filter: $filter, first: 1) {
			nodes { id }
		}
	}
	"""
	try:
		data = _linear_request(
			api_key, gql, {"filter": {"identifier": {"eq": identifier}}}
		)
		nodes = data.get("data", {}).get("issues", {}).get("nodes", [])
		return nodes[0]["id"] if nodes else None
	except Exception:
		return None


def post_linear_comment(entry_name: str):
	"""Post a comment on the linked Linear issue.  Silent on failure."""
	try:
		entry = frappe.get_doc("Watch Entry", entry_name)
		api_key = frappe.db.get_single_value("Watch Settings", "linear_api_key")
		if not api_key or not entry.linear_issue:
			return
		if not frappe.db.get_single_value("Watch Settings", "linear_post_comment"):
			return

		issue_id = _resolve_linear_issue_id(entry.linear_issue, api_key)
		if not issue_id:
			return

		body = (
			f"\u23f1 {_format_duration(entry.duration_hours)} logged: "
			f"{entry.description or _('(no description)')}"
		)

		gql = """
		mutation($issueId: String!, $body: String!) {
			commentCreate(input: {issueId: $issueId, body: $body}) { success }
		}
		"""
		_linear_request(api_key, gql, {"issueId": issue_id, "body": body})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch Linear comment failed")


# ── GitHub ───────────────────────────────────────────────────────────────


@frappe.whitelist()
def test_github() -> dict:
	"""Validate the GitHub token; returns username."""
	if not "System Manager" in frappe.get_roles():
		frappe.throw(_("Only System Manager can test integrations"), frappe.PermissionError)

	token = frappe.db.get_single_value("Watch Settings", "github_token")
	if not token:
		frappe.throw(_("No GitHub token configured"))

	resp = requests.get(
		"https://api.github.com/user",
		headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
		timeout=5,
	)
	resp.raise_for_status()
	user = resp.json().get("login", "")
	return {"status": "ok", "username": user}


@frappe.whitelist()
def search_github_issues(query: str) -> list:
	"""Search GitHub issues and PRs by number or title."""
	token = frappe.db.get_single_value("Watch Settings", "github_token")
	default_repo = frappe.db.get_single_value("Watch Settings", "github_default_repo")
	if not token or not default_repo or len(query) < 1:
		return []

	try:
		resp = requests.get(
			"https://api.github.com/search/issues",
			headers={
				"Authorization": f"Bearer {token}",
				"Accept": "application/vnd.github+json",
			},
			params={"q": f"{query} repo:{default_repo}", "per_page": 10},
			timeout=5,
		)
		resp.raise_for_status()
		items = resp.json().get("items", [])
		return [
			{
				"value": f"#{i['number']}",
				"label": f"#{i['number']}: {i['title']}",
				"url": i["html_url"],
			}
			for i in items
		]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch GitHub search failed")
		return []


def post_github_comment(entry_name: str):
	"""Post a comment on the linked GitHub issue or PR.  Silent on failure."""
	try:
		entry = frappe.get_doc("Watch Entry", entry_name)
		token = frappe.db.get_single_value("Watch Settings", "github_token")
		default_repo = frappe.db.get_single_value("Watch Settings", "github_default_repo")
		if not token or not entry.github_ref:
			return
		if not frappe.db.get_single_value("Watch Settings", "github_post_comment"):
			return

		ref = entry.github_ref
		if "/" in ref:
			repo, number = ref.rsplit("#", 1)
		else:
			repo = default_repo
			number = ref.lstrip("#")

		if not repo or not number:
			return

		body = (
			f"\u23f1 {_format_duration(entry.duration_hours)} logged: "
			f"{entry.description or _('(no description)')}"
		)

		requests.post(
			f"https://api.github.com/repos/{repo}/issues/{number}/comments",
			headers={
				"Authorization": f"Bearer {token}",
				"Accept": "application/vnd.github+json",
			},
			json={"body": body},
			timeout=5,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Watch GitHub comment failed")
