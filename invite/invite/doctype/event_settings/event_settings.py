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
	return {
		"default_currency": settings.default_currency,
		"default_event_type": settings.default_event_type,
		"default_reminder_days": settings.default_reminder_days,
		"app_name": settings.app_name,
		"app_logo": settings.app_logo,
		"whatsapp_provider": getattr(settings, "whatsapp_provider", ""),
		"whatsapp_phone_number_id": getattr(settings, "whatsapp_phone_number_id", ""),
		"whatsapp_business_number": getattr(settings, "whatsapp_business_number", ""),
		"whatsapp_api_version": getattr(settings, "whatsapp_api_version", "v21.0"),
	}
