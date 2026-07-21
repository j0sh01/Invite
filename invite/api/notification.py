# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_notifications():
	"""Get notifications for the current user."""
	user = frappe.session.user

	notifications = frappe.get_all(
		"Notification Log",
		filters={
			"for_user": user,
			"type": "Alert",
		},
		fields=[
			"name", "subject", "email_content", "document_type",
			"document_name", "read", "creation", "from_user"
		],
		order_by="creation DESC",
		limit=50,
	)

	result = []
	for n in notifications:
		from_user_name = ""
		if n.from_user:
			from_user_name = frappe.db.get_value("User", n.from_user, "full_name") or n.from_user

		result.append({
			"name": n.name,
			"notification_text": n.subject or n.email_content,
			"read": n.read or 0,
			"creation": str(n.creation),
			"reference_doctype": n.document_type,
			"reference_name": n.document_name,
			"from_user": {
				"name": n.from_user,
				"full_name": from_user_name,
			},
			"route_name": n.document_type,
			"hash": "",
		})

	return result


@frappe.whitelist()
def mark_as_read(doc=None):
	"""Mark a notification as read. If doc is None, mark all as read."""
	if doc:
		frappe.db.set_value("Notification Log", doc, "read", 1)
	else:
		frappe.db.set_value(
			"Notification Log",
			{"for_user": frappe.session.user, "read": 0},
			"read",
			1,
		)
	frappe.db.commit()
	return {"success": True}
