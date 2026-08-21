# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document


class InviteActivityLog(Document):
	pass


CATEGORY_MAP = {
	"Guest Created": "Guest Management",
	"Guest Updated": "Guest Management",
	"Guest Deleted": "Guest Management",
	"Guest Imported": "Guest Management",
	"Invitation Created": "Invitation",
	"Invitation Sent": "Invitation",
	"Invitation Failed": "Invitation",
	"Invitation Card Generated": "Card",
	"QR Code Generated": "Card",
	"RSVP Submitted": "RSVP",
	"RSVP Updated": "RSVP",
	"Check-In (QR Scan)": "Check-In",
	"Check-In (Manual)": "Check-In",
	"Check-In (Invite Code)": "Check-In",
	"Duplicate Scan": "Check-In",
	"Reminder Sent": "Communication",
	"Thank You Sent": "Communication",
	"Card Downloaded": "Card",
	"Frontdesk Scan Started": "Frontdesk",
	"Event Updated": "System",
}


def log_action(event, action_type, subject, guest=None, guest_name=None,
               details=None, reference_doctype=None, reference_name=None,
               extra_data=None):
	"""Log an activity to the audit trail.

	This is the primary function to call from anywhere in the invite app.

	Args:
	    event: Event document name
	    action_type: One of the Select options in action_type field
	    subject: Short description of the action
	    guest: Guest document name (optional)
	    guest_name: Guest full name (optional, for display)
	    details: Longer description (optional)
	    reference_doctype: Linked doctype name (optional)
	    reference_name: Linked document name (optional)
	    extra_data: Dict of additional data to store as JSON (optional)
	"""
	category = CATEGORY_MAP.get(action_type, "System")

	ip = None
	try:
		ip = frappe.local.request_ip or frappe.get_request_header("X-Forwarded-For")
	except Exception:
		pass

	doc = frappe.get_doc({
		"doctype": "Invite Activity Log",
		"event": event,
		"guest": guest,
		"guest_name": guest_name,
		"action_type": action_type,
		"action_category": category,
		"subject": subject,
		"details": details or "",
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"performed_by": frappe.session.user,
		"ip_address": ip,
		"extra_data": json.dumps(extra_data) if extra_data else None,
	})

	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.name
