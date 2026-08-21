# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventSettings(Document):
	pass


@frappe.whitelist()
def get_event_settings():
	"""Get event settings for the frontend."""
	settings = frappe.get_single("Event Settings")

	def _pwd(field):
		"""Get decrypted password value, returning empty string if unset."""
		try:
			return settings.get_password(field) or ""
		except Exception:
			return ""

	return {
		"default_currency": settings.default_currency,
		"default_event_type": settings.default_event_type,
		"default_reminder_days": settings.default_reminder_days,
		"qr_code_foreground_color": getattr(settings, "qr_code_foreground_color", "#000000"),
		"qr_code_background_color": getattr(settings, "qr_code_background_color", "#FFFFFF"),
		"qr_code_size": getattr(settings, "qr_code_size", 8),
		"whatsapp_provider": getattr(settings, "whatsapp_provider", ""),
		"whatsapp_api_key": _pwd("whatsapp_api_key"),
		"whatsapp_phone_number_id": getattr(settings, "whatsapp_phone_number_id", ""),
		"whatsapp_business_number": getattr(settings, "whatsapp_business_number", ""),
		"whatsapp_api_version": getattr(settings, "whatsapp_api_version", "v21.0"),
		"twilio_account_sid": getattr(settings, "twilio_account_sid", ""),
		"twilio_auth_token": _pwd("twilio_auth_token"),
		"twilio_whatsapp_number": getattr(settings, "twilio_whatsapp_number", ""),
		"twilio_template_invitation": getattr(settings, "twilio_template_invitation", ""),
		"twilio_template_rsvp_confirm": getattr(settings, "twilio_template_rsvp_confirm", ""),
		"twilio_template_rsvp_reminder": getattr(settings, "twilio_template_rsvp_reminder", ""),
		"twilio_template_event_reminder": getattr(settings, "twilio_template_event_reminder", ""),
		"twilio_template_event_update": getattr(settings, "twilio_template_event_update", ""),
		"twilio_template_qr_checkin": getattr(settings, "twilio_template_qr_checkin", ""),
		"twilio_template_thank_you": getattr(settings, "twilio_template_thank_you", ""),
		"google_client_id": getattr(settings, "google_client_id", ""),
		"google_client_secret": _pwd("google_client_secret"),
		"frontdesk_role": getattr(settings, "frontdesk_role", ""),
	}


EVENT_SETTINGS_FIELDS = [
	"default_currency",
	"default_event_type",
	"default_reminder_days",
	"qr_code_foreground_color",
	"qr_code_background_color",
	"qr_code_size",
	"whatsapp_provider",
	"whatsapp_api_key",
	"whatsapp_phone_number_id",
	"whatsapp_business_number",
	"whatsapp_api_version",
	"twilio_account_sid",
	"twilio_auth_token",
	"twilio_whatsapp_number",
	"twilio_template_invitation",
	"twilio_template_rsvp_confirm",
	"twilio_template_rsvp_reminder",
	"twilio_template_event_reminder",
	"twilio_template_event_update",
	"twilio_template_qr_checkin",
	"twilio_template_thank_you",
	"google_client_id",
	"google_client_secret",
	"frontdesk_role",
]


@frappe.whitelist(allow_guest=False)
def save_event_settings(**kwargs):
	"""Save event settings fields using the Document API.

	Uses ignore_is_latest to bypass the TimestampMismatchError check,
	while still properly encrypting Password fields (twilio_auth_token,
	whatsapp_api_key, google_client_secret).

	Accepts field values as keyword arguments (from frappe.form_dict).
	Only updates fields that are in EVENT_SETTINGS_FIELDS.
	"""
	if not frappe.has_permission("Event Settings", "write"):
		frappe.throw("Not permitted to update Event Settings")

	doc = frappe.get_doc("Event Settings")
	updates = {k: v for k, v in kwargs.items() if k in EVENT_SETTINGS_FIELDS and v is not None}
	if updates:
		for field, value in updates.items():
			doc.set(field, value)
		doc.flags.ignore_is_latest = True
		doc.save()
	return doc
