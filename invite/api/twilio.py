# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

"""
Twilio WhatsApp Integration

Uses Twilio's Content API (Content Template Builder) for sending messages.
The old "WhatsApp Templates" system has been replaced by the Content API.

Requirements (set in Event Settings > Twilio Settings):
- whatsapp_provider: "Twilio"
- twilio_account_sid: Your Twilio Account SID
- twilio_auth_token: Your Twilio Auth Token
- twilio_whatsapp_number: Your Twilio WhatsApp-enabled number

Message Templates (created in Twilio Content Template Builder):
- Event Invitation: Send event details with RSVP link
- RSVP Confirmation: Confirm guest's RSVP response
- RSVP Reminder: Remind guests to respond
- Event Reminder: Remind about upcoming event
- Event Update: Notify about event changes
- QR/Check-in Message: Send QR code for check-in
- Thank You: Post-event thank you message
"""

import frappe
import requests
import base64


def get_twilio_config():
	"""Get Twilio API configuration from Event Settings."""
	settings = frappe.get_single("Event Settings")

	# IMPORTANT: twilio_auth_token is a Password field —
	# getattr() returns the encrypted value.  We must use
	# get_password() to get the decrypted plaintext.
	try:
		auth_token = settings.get_password("twilio_auth_token") or ""
	except Exception:
		auth_token = ""

	return {
		"enabled": (
			getattr(settings, "whatsapp_provider", "") == "Twilio"
			and getattr(settings, "twilio_account_sid", "")
			and auth_token
		),
		"account_sid": getattr(settings, "twilio_account_sid", ""),
		"auth_token": auth_token,
		"whatsapp_number": getattr(settings, "twilio_whatsapp_number", ""),
	}


def send_whatsapp_message(to_number, message, media_url=None):
	"""Send a WhatsApp message via Twilio.

	Uses the Messages API with a simple text body.
	For template-based messages, use send_template_message() instead.

	Args:
		to_number: Recipient phone number (with country code)
		message: Message text body
		media_url: Optional media URL to attach (image/document)

	Returns:
		bool: True if sent successfully
	"""
	config = get_twilio_config()
	if not config["enabled"]:
		frappe.log_error("Twilio API not configured", "Twilio Integration")
		return False

	# Ensure WhatsApp prefix
	if not to_number.startswith("whatsapp:"):
		to_number_clean = to_number.replace("+", "").replace(" ", "")
		to_number = f"whatsapp:+{to_number_clean}"

	from_number = config["whatsapp_number"]
	if not from_number.startswith("whatsapp:"):
		from_number_clean = from_number.replace("+", "").replace(" ", "")
		from_number = f"whatsapp:+{from_number_clean}"

	url = f"https://api.twilio.com/2010-04-01/Accounts/{config['account_sid']}/Messages.json"

	payload = {
		"From": from_number,
		"To": to_number,
		"Body": message,
	}

	with_media = False
	if media_url:
		# Twilio downloads the media from this URL on its own servers. A
		# local-only host (e.g. http://mchango:8000) can never be fetched by
		# Twilio: the API still accepts the message and returns a SID, but
		# delivery then fails asynchronously with error 63019 ("Media failed
		# to download"). Detect that up front and bail out so the caller's
		# fallback chain (template → plain text) runs instead of silently
		# dropping the message.
		if not _is_publicly_reachable_url(media_url):
			frappe.logger().info(
				f"Skipping Twilio media attachment {media_url} for {to_number}: "
				"host is not publicly reachable"
			)
			return False
		# File URLs from Frappe keep raw spaces/parentheses (e.g.
		# "/files/Pasted image (10).png"); Twilio's downloader chokes on
		# unencoded characters and the message then fails with 63019 even
		# though the file exists. Encode the path before handing it over.
		payload["MediaUrl"] = _encode_media_url(media_url)
		with_media = True

	try:
		response = requests.post(
			url,
			data=payload,
			auth=(config["account_sid"], config["auth_token"]),
			timeout=30,
		)
		response.raise_for_status()
		result = response.json()
		if result.get("sid"):
			frappe.logger().info(f"Twilio WhatsApp accepted to {to_number}, SID: {result['sid']}")
			# Twilio accepts the message and returns a SID even when the
			# recipient can never receive it (e.g. a number that has not joined
			# the sandbox fails asynchronously with 63015, media it cannot
			# download with 63019). Confirm against the real message status so
			# callers do not report a phantom "sent".
			if _poll_message_status(result["sid"], timeout=15 if with_media else 8):
				return True
			# The media send settled on failed (bad file, unsupported type,
			# download error) — never leave the guest without a message:
			# retry the same text with no attachment.
			if with_media:
				frappe.logger().warning(
					f"Twilio media message {result['sid']} to {to_number} failed; "
					"retrying as plain text without the attachment"
				)
				text_payload = {
					"From": from_number,
					"To": to_number,
					"Body": message,
				}
				retry = requests.post(
					url,
					data=text_payload,
					auth=(config["account_sid"], config["auth_token"]),
					timeout=30,
				)
				retry.raise_for_status()
				retry_result = retry.json()
				if retry_result.get("sid"):
					return _poll_message_status(retry_result["sid"])
		return False
	except requests.exceptions.RequestException as e:
		error_detail = str(e)
		try:
			error_detail = e.response.json().get("message", str(e))
		except Exception:
			pass
		frappe.log_error(f"Twilio WhatsApp send failed: {error_detail}", "Twilio Integration")
		return False


def _poll_message_status(message_sid, timeout=8):
	"""Wait briefly for a Twilio message to leave the transient states.

	A message Twilio just accepted is usually ``queued``; recipients that can
	never receive it (not in the sandbox, bad number) settle on ``failed``
	within a second or two. Poll until a terminal status appears:

	- ``sent`` / ``delivered`` / ``read`` → True (deliverable)
	- ``failed`` / ``undelivered`` → False (never delivered)
	- still ``queued``/``accepted``/``sending`` after the timeout → True
	  (assume normal delivery proceeds)
	"""
	import time

	config = get_twilio_config()
	url = f"https://api.twilio.com/2010-04-01/Accounts/{config['account_sid']}/Messages/{message_sid}.json"
	deadline = time.time() + timeout
	terminal_ok = {"sent", "delivered", "read"}
	terminal_fail = {"failed", "undelivered"}

	while time.time() < deadline:
		try:
			response = requests.get(
				url,
				auth=(config["account_sid"], config["auth_token"]),
				timeout=10,
			)
			response.raise_for_status()
			data = response.json()
			status = (data or {}).get("status", "")
			if status in terminal_ok:
				frappe.logger().info(f"Twilio message {message_sid} status: {status}")
				return True
			if status in terminal_fail:
				error_code = data.get("error_code") or ""
				error_message = data.get("error_message") or ""
				frappe.log_error(
					f"Twilio message {message_sid} {status}: {error_code} {error_message}",
					"Twilio Integration",
				)
				return False
		except Exception:
			pass
		time.sleep(1)

	frappe.logger().info(f"Twilio message {message_sid} still {status or 'transient'} after {timeout}s - assuming delivery proceeds")
	return True


def _get_template_variables(content_sid):
	"""Fetch a Content API template's variable names, cached per SID.

	The Content API renders placeholders by NAME ({{first_name}}), while the
	app historically sent numbered variables ({{1}}, {{2}}...). Knowing the
	template's variable names lets callers map values positionally so any
	well-formed template renders correctly.

	Returns a dict of variable-name → default value, or {} when the schema
	could not be fetched (callers then fall back to legacy behaviour).
	"""
	cache_key = f"twilio_template_vars:{content_sid}"
	cached = frappe.cache().get_value(cache_key)
	if cached is not None:
		return cached

	config = get_twilio_config()
	try:
		response = requests.get(
			f"https://content.twilio.com/v1/Content/{content_sid}",
			auth=(config["account_sid"], config["auth_token"]),
			timeout=15,
		)
		response.raise_for_status()
		data = response.json()
		variables = {}
		for t in (data.get("types") or {}).values():
			variables.update(t.get("variables") or {})
		if not variables:
			variables = data.get("variables") or {}
		frappe.cache().set_value(cache_key, variables, expires_in_sec=3600)
		return variables
	except Exception:
		return {}


def _is_publicly_reachable_url(url):
	"""Best-effort check that a media URL can be fetched from the public internet.

	Twilio WhatsApp attachments must be downloadable by Twilio's servers, so
	the host has to resolve publicly. Local-only hosts — ``localhost``, bare
	hostnames with no dot (e.g. ``mchango``), and private/reserved IPs — can
	never be reached by Twilio and would fail with error 63019 after the
	message is accepted.
	"""
	import re
	from urllib.parse import urlparse

	try:
		host = (urlparse(url).hostname or "").lower().rstrip(".")
	except Exception:
		return False
	if not host:
		return False
	if host == "localhost" or host.endswith(".local"):
		return False
	# A bare hostname without a dot ("mchango") is not a public DNS name.
	if "." not in host:
		return False
	# Private / reserved IP ranges (10.x, 127.x, 169.254.x, 172.16-31.x, 192.168.x)
	if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
		parts = host.split(".")
		first, second = int(parts[0]), int(parts[1])
		if (
			first in (0, 10, 127)
			or (first == 169 and second == 254)
			or (first == 172 and 16 <= second <= 31)
			or (first == 192 and second == 168)
		):
			return False
	return True


def _encode_media_url(url):
	"""Percent-encode the path of a media URL for Twilio's downloader.

	Frappe file URLs keep raw spaces and parentheses (e.g.
	``/files/Pasted image (10).png``). Twilio's servers must fetch the URL
	themselves and fail with 63019 on unencoded characters, so encode the
	path while leaving the scheme/host and any query string intact.
	"""
	from urllib.parse import quote, urlsplit, urlunsplit

	try:
		parts = urlsplit(url)
		path = quote(parts.path, safe="/%:@")
		query = quote(parts.query, safe="=&%")
		return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))
	except Exception:
		return url


def send_template_message(to_number, content_sid, template_variables=None):
	"""Send a WhatsApp template message via Twilio Content API.

	This uses Twilio's Content Template Builder templates.
	Create templates at: https://console.twilio.com/us1/develop/sms/content-api

	Args:
		to_number: Recipient phone number (with country code)
		content_sid: Content SID from Twilio Content Template Builder
		template_variables: Dict of template variables (e.g., {"1": "John", "2": "Wedding"})

	Returns:
		bool: True if sent successfully
	"""
	config = get_twilio_config()
	if not config["enabled"]:
		frappe.log_error("Twilio API not configured", "Twilio Integration")
		return False

	# Ensure WhatsApp prefix
	if not to_number.startswith("whatsapp:"):
		to_number_clean = to_number.replace("+", "").replace(" ", "")
		to_number = f"whatsapp:+{to_number_clean}"

	from_number = config["whatsapp_number"]
	if not from_number.startswith("whatsapp:"):
		from_number_clean = from_number.replace("+", "").replace(" ", "")
		from_number = f"whatsapp:+{from_number_clean}"

	url = f"https://api.twilio.com/2010-04-01/Accounts/{config['account_sid']}/Messages.json"

	payload = {
		"From": from_number,
		"To": to_number,
		"ContentSid": content_sid,
	}

	# Add template variables if provided.
	# Variables are JSON-encoded for Twilio's Content API. DB values can arrive
	# as non-JSON types (e.g. Time fields come back as datetime.timedelta), so
	# coerce every value to a string before encoding.
	if template_variables:
		import json
		safe_variables = {
			str(key): (str(value) if not isinstance(value, str) else value)
			for key, value in template_variables.items()
		}
		# Twilio's Content API renders placeholders by NAME ({{first_name}}),
		# not the numbered {{1}}/{{2}} convention of the old WhatsApp
		# Templates. Fetch the template's variable names and map our values
		# onto them positionally so any well-formed template renders correctly.
		schema = _get_template_variables(content_sid)
		if schema:
			names = list(schema.keys())
			values = [safe_variables[k] for k in sorted(safe_variables, key=int)]
			if len(names) != len(values):
				frappe.logger().warning(
					f"Template {content_sid} expects {len(names)} variable(s) "
					f"({', '.join(names)}) but {len(values)} value(s) were provided; "
					"falling back to plain text instead of sending wrong content."
				)
				return False
			payload["ContentVariables"] = json.dumps(dict(zip(names, values)))
		else:
			# Template schema could not be fetched — send the numbered
			# variables as before (works for templates whose variables are
			# literally named 1, 2, 3...).
			payload["ContentVariables"] = json.dumps(safe_variables)

	try:
		response = requests.post(
			url,
			data=payload,
			auth=(config["account_sid"], config["auth_token"]),
			timeout=30,
		)
		response.raise_for_status()
		result = response.json()
		if result.get("sid"):
			frappe.logger().info(f"Twilio template accepted to {to_number}, SID: {result['sid']}")
			# Same async-failure caveat as plain messages - confirm real status.
			return _poll_message_status(result["sid"])
		return False
	except requests.exceptions.RequestException as e:
		error_detail = str(e)
		try:
			error_detail = e.response.json().get("message", str(e))
		except Exception:
			pass
		frappe.log_error(f"Twilio template send failed: {error_detail}", "Twilio Integration")
		return False


def send_media_message(to_number, message, media_url):
	"""Send a WhatsApp message with media attachment via Twilio.

	Args:
		to_number: Recipient phone number (with country code)
		message: Message text caption
		media_url: URL of the media to send (must be publicly accessible)

	Returns:
		bool: True if sent successfully
	"""
	return send_whatsapp_message(to_number, message, media_url=media_url)


# ──────────────────────────────────────────────
#  Template SIDs (configure in Twilio Console)
# ──────────────────────────────────────────────

def get_template_sids():
	"""Get template SIDs from Event Settings.

	These are Content SIDs from Twilio's Content Template Builder.
	Create templates at: https://console.twilio.com/us1/develop/sms/content-api

	Returns dict of template names to Content SIDs.
	"""
	return {
		"event_invitation": frappe.db.get_single_value("Event Settings", "twilio_template_invitation") or "",
		"rsvp_confirmation": frappe.db.get_single_value("Event Settings", "twilio_template_rsvp_confirm") or "",
		"rsvp_reminder": frappe.db.get_single_value("Event Settings", "twilio_template_rsvp_reminder") or "",
		"event_reminder": frappe.db.get_single_value("Event Settings", "twilio_template_event_reminder") or "",
		"event_update": frappe.db.get_single_value("Event Settings", "twilio_template_event_update") or "",
		"qr_checkin": frappe.db.get_single_value("Event Settings", "twilio_template_qr_checkin") or "",
		"thank_you": frappe.db.get_single_value("Event Settings", "twilio_template_thank_you") or "",
	}


# ──────────────────────────────────────────────
#  Connection Testing & Diagnostics
# ──────────────────────────────────────────────


@frappe.whitelist()
def test_connection():
	"""Test Twilio API connection by fetching account details.

	Returns:
		 dict with diagnostics about the Twilio configuration.
	"""
	settings = frappe.get_single("Event Settings")
	provider = getattr(settings, "whatsapp_provider", "")
	sid = getattr(settings, "twilio_account_sid", "")
	try:
		auth_token = settings.get_password("twilio_auth_token") or ""
	except Exception:
		auth_token = ""
	number = getattr(settings, "twilio_whatsapp_number", "")

	# ── Step 1: Validate that all fields are present ──
	missing = []
	if provider != "Twilio":
		missing.append(f"whatsapp_provider (currently: '{provider}')")
	if not sid:
		missing.append("twilio_account_sid")
	if not auth_token:
		missing.append("twilio_auth_token")
	if not number:
		missing.append("twilio_whatsapp_number")

	if missing:
		return {
			"success": False,
			"error": f"Missing fields: {', '.join(missing)}",
			"diagnostics": {
				"provider": provider,
				"account_sid_masked": f"{sid[:6]}...{sid[-4:]}" if len(sid) > 10 else (sid or "(empty)"),
				"auth_token_set": bool(auth_token),
				"whatsapp_number": number or "(empty)",
			}
		}

	# ── Step 2: Verify credentials with Twilio API ──
	try:
		url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json"
		response = requests.get(url, auth=(sid, auth_token), timeout=15)
		response.raise_for_status()
		account = response.json()

		# Fetch WhatsApp-enabled phone numbers
		phones_url = (
			f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json"
			f"?PhoneNumber={number.replace('+', '').replace(' ', '')}"
		)
		phones_resp = requests.get(phones_url, auth=(sid, auth_token), timeout=15)
		phones = phones_resp.json().get("incoming_phone_numbers", []) if phones_resp.ok else []

		return {
			"success": True,
			"account_name": account.get("friendly_name", ""),
			"account_status": account.get("status", ""),
			"balance": account.get("balance", ""),
			"whatsapp_number": number,
			"phone_numbers_found": len(phones),
		}

	except requests.exceptions.RequestException as e:
		error_code = e.response.status_code if e.response is not None else None
		error_detail = str(e)
		try:
			error_detail = e.response.json().get("message", str(e))
		except Exception:
			pass

		# Provide actionable guidance based on error code
		guidance = ""
		if error_code == 401:
			guidance = (
				"HTTP 401 = Invalid credentials. "
				"Double-check your Account SID (starts with AC) and Auth Token "
				"on https://console.twilio.com → Account → API keys & tokens. "
				"Make sure you're using the AUTH TOKEN, not an API key."
			)
		elif error_code == 404:
			guidance = (
				"HTTP 404 = Account not found. "
				"Your Account SID may be wrong. It starts with 'AC'."
			)
		else:
			guidance = f"HTTP {error_code or '?'}: {error_detail}"

		return {
			"success": False,
			"error": guidance,
			"diagnostics": {
				"account_sid_masked": f"{sid[:6]}...{sid[-4:]}" if len(sid) > 10 else sid,
				"auth_token_length": len(auth_token),
				"whatsapp_number": number,
				"http_status": error_code,
			}
		}


@frappe.whitelist()
def list_content_templates():
	"""Fetch available Content Templates from Twilio Content API.

	Returns:
		 list of dicts with template sid, name, language, channel, and variables.
	"""
	config = get_twilio_config()
	if not config["enabled"]:
		frappe.log_error(
			"Cannot list templates: Twilio is not configured. "
			"Ensure whatsapp_provider='Twilio', twilio_account_sid, and twilio_auth_token are set.",
			"Twilio Integration",
		)
		return []

	try:
		url = f"https://content.twilio.com/v1/ContentTemplates"
		response = requests.get(
			url,
			auth=(config["account_sid"], config["auth_token"]),
			timeout=15,
		)
		response.raise_for_status()
		templates = response.json().get("templates", [])

		result = []
		for t in templates:
			result.append({
				"sid": t.get("sid", ""),
				"friendly_name": t.get("friendly_name", ""),
				"language": t.get("language", ""),
				"channel": t.get("channel", ""),
				"date_created": t.get("date_created", ""),
				"date_updated": t.get("date_updated", ""),
			})
		return result

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"Failed to fetch Twilio content templates: {e}", "Twilio Integration")
		return []


@frappe.whitelist()
def send_test_message(to_number, template_sid=None, message=None):
	"""Send a test WhatsApp message to verify the connection works.

	If template_sid is provided, sends via Content API with that template.
	Otherwise sends a plain text test message.

	Args:
		to_number: Recipient phone number (with country code)
		template_sid: Optional Content SID for template-based test
		message: Optional plain text message (default: test message)

	Returns:
		 dict with success, message_sid, and any error.
	"""
	config = get_twilio_config()
	if not config["enabled"]:
		return {
			"success": False,
			"error": "Twilio is not configured. Set WhatsApp Provider to 'Twilio' and fill in credentials.",
		}

	if not to_number:
		return {"success": False, "error": "Recipient phone number is required."}

	if template_sid:
		# Send via Content API with template
		template_variables = {
			"1": "Test Guest",
			"2": "Test Event",
			"3": "2026-12-31",
			"4": "12:00 PM",
			"5": "Test Venue",
			"6": "https://example.com/rsvp",
		}
		sent = send_template_message(to_number, template_sid, template_variables)
		if sent:
			return {"success": True, "message": f"Test template message sent to {to_number}", "method": "template"}
		else:
			return {"success": False, "error": "Failed to send template message. Check template SID and variables."}
	else:
		# Send plain text test
		test_msg = message or "✅ Invite App test message from Twilio. If you see this, your WhatsApp integration is working!"
		sent = send_whatsapp_message(to_number, test_msg)
		if sent:
			return {"success": True, "message": f"Test message sent to {to_number}", "method": "text"}
		else:
			return {"success": False, "error": "Failed to send test message. Check Twilio credentials and phone number."}
