# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MessageTemplate(Document):
	def validate(self):
		self.set_default_variables()

	def set_default_variables(self):
		"""Set the available variables hint."""
		if not self.available_variables:
			self.available_variables = (
				"{guest_name} - Guest's full name\n"
				"{event_name} - Event name\n"
				"{event_date} - Event date\n"
				"{event_time} - Event time\n"
				"{venue} - Event venue\n"
				"{rsvp_link} - RSVP response link\n"
				"{invite_code} - Guest's invite code"
			)


def render_template(template_body, context):
	"""Render a message template with the given context.

	Args:
		template_body: The template body string with placeholders
		context: Dict of variable replacements

	Returns:
		str: The rendered message
	"""
	if not template_body:
		return ""

	message = template_body
	for key, value in context.items():
		message = message.replace(f"{{{key}}}", str(value or ""))

	return message


@frappe.whitelist()
def get_template(template_type, channel="WhatsApp"):
	"""Get an active template by type and channel."""
	template = frappe.db.get_value(
		"Message Template",
		{"template_type": template_type, "channel": channel, "enabled": 1},
		["name", "subject", "body", "twilio_content_sid"],
		as_dict=True,
	)
	return template


@frappe.whitelist()
def get_all_templates():
	"""Get all active templates."""
	return frappe.get_all(
		"Message Template",
		filters={"enabled": 1},
		fields=["name", "template_name", "template_type", "channel", "subject", "body", "twilio_content_sid"],
		order_by="template_type ASC",
	)
