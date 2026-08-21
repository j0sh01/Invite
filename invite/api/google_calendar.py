# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

"""
Google Calendar Integration

Syncs events with Google Calendar for organizers and guests.
Uses OAuth 2.0 for authentication with Google APIs.

Setup:
1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials (Web application)
4. Set redirect URI to: {site_url}/api/method/invite.api.google_calendar.oauth_callback
5. Store Client ID and Client Secret in Event Settings
"""

import frappe
from frappe.utils import get_url, cint


def get_google_config():
	"""Get Google Calendar configuration from Event Settings."""
	settings = frappe.get_single("Event Settings")
	return {
		"client_id": getattr(settings, "google_client_id", ""),
		"client_secret": getattr(settings, "google_client_secret", ""),
		"enabled": bool(getattr(settings, "google_client_id", "")),
	}


@frappe.whitelist()
def get_auth_url():
	"""Get Google OAuth authorization URL."""
	config = get_google_config()
	if not config["enabled"]:
		frappe.throw("Google Calendar integration is not configured.")

	from urllib.parse import urlencode

	redirect_uri = f"{get_url()}/api/method/invite.api.google_calendar.oauth_callback"

	params = {
		"client_id": config["client_id"],
		"redirect_uri": redirect_uri,
		"response_type": "code",
		"scope": "https://www.googleapis.com/auth/calendar",
		"access_type": "offline",
		"prompt": "consent",
	}

	auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
	return {"auth_url": auth_url}


@frappe.whitelist(allow_guest=True)
def oauth_callback():
	"""Handle Google OAuth callback."""
	code = frappe.form_dict.get("code")
	if not code:
		frappe.throw("Authorization failed: No code received.")

	config = get_google_config()
	redirect_uri = f"{get_url()}/api/method/invite.api.google_calendar.oauth_callback"

	# Exchange code for tokens
	import requests
	token_url = "https://oauth2.googleapis.com/token"
	token_data = {
		"code": code,
		"client_id": config["client_id"],
		"client_secret": config["client_secret"],
		"redirect_uri": redirect_uri,
		"grant_type": "authorization_code",
	}

	try:
		response = requests.post(token_url, data=token_data, timeout=30)
		response.raise_for_status()
		tokens = response.json()

		# Store tokens for current user
		user = frappe.session.user
		frappe.db.set_value("User", user, {
			"google_calendar_access_token": tokens.get("access_token"),
			"google_calendar_refresh_token": tokens.get("refresh_token"),
			"google_calendar_token_expiry": tokens.get("expires_in"),
		})
		frappe.db.commit()

		frappe.response["type"] = "redirect"
		frappe.response["location"] = f"{get_url()}/invite/events"

	except Exception as e:
		frappe.log_error(f"Google OAuth callback failed: {e}", "Google Calendar")
		frappe.throw("Failed to complete Google authentication.")


def get_valid_token():
	"""Get a valid Google access token, refreshing if needed."""
	user = frappe.session.user
	access_token = frappe.db.get_value("User", user, "google_calendar_access_token")
	refresh_token = frappe.db.get_value("User", user, "google_calendar_refresh_token")

	if not access_token or not refresh_token:
		return None

	# Try to use the access token
	return access_token


@frappe.whitelist()
def sync_event_to_calendar(event_name):
	"""Sync an event to Google Calendar."""
	access_token = get_valid_token()
	if not access_token:
		frappe.throw("Google Calendar is not connected. Please connect first.")

	event_doc = frappe.get_doc("Event", event_name)

	# Build Google Calendar event
	calendar_event = {
		"summary": event_doc.event_name,
		"description": f"{event_doc.description or ''}\n\nVenue: {event_doc.venue or 'TBD'}",
		"start": {
			"date": str(event_doc.event_date),
			"timeZone": frappe.db.get_default("time_zone") or "Africa/Dar_es_Salaam",
		},
		"end": {
			"date": str(event_doc.event_date),
			"timeZone": frappe.db.get_default("time_zone") or "Africa/Dar_es_Salaam",
		},
	}

	if event_doc.venue:
		calendar_event["location"] = f"{event_doc.venue}, {event_doc.location_address or ''}"

	if event_doc.event_time:
		calendar_event["start"]["dateTime"] = f"{event_doc.event_date}T{event_doc.event_time}"
		del calendar_event["start"]["date"]
		calendar_event["end"]["dateTime"] = f"{event_doc.event_date}T{event_doc.event_time}"
		del calendar_event["end"]["date"]

	# Create event in Google Calendar
	import requests
	url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
	headers = {
		"Authorization": f"Bearer {access_token}",
		"Content-Type": "application/json",
	}

	try:
		response = requests.post(url, json=calendar_event, headers=headers, timeout=30)
		response.raise_for_status()
		result = response.json()

		# Store the Google event ID on our event
		event_doc.db_set("google_calendar_event_id", result.get("id"))

		return {
			"success": True,
			"google_event_id": result.get("id"),
			"html_link": result.get("htmlLink"),
		}

	except requests.exceptions.RequestException as e:
		error_detail = str(e)
		try:
			error_detail = e.response.json().get("error", {}).get("message", str(e))
		except Exception:
			pass
		frappe.log_error(f"Google Calendar sync failed: {error_detail}", "Google Calendar")
		frappe.throw(f"Failed to sync to Google Calendar: {error_detail}")


@frappe.whitelist()
def disconnect_calendar():
	"""Disconnect Google Calendar for current user."""
	user = frappe.session.user
	frappe.db.set_value("User", user, {
		"google_calendar_access_token": "",
		"google_calendar_refresh_token": "",
		"google_calendar_token_expiry": "",
	})
	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def get_connection_status():
	"""Check if Google Calendar is connected."""
	access_token = frappe.db.get_value("User", frappe.session.user, "google_calendar_access_token")
	return {"connected": bool(access_token)}
