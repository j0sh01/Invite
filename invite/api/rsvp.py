# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe


def on_update(doc, method=None):
	if doc.guest:
		guest = frappe.get_doc("Guest", doc.guest)
		guest.rsvp_status = doc.rsvp_status
		guest.rsvp_date = doc.response_date
		guest.number_of_attendees = doc.number_of_attendees
		guest.save(ignore_permissions=True)

	if doc.invitation:
		inv = frappe.get_doc("Invitation", doc.invitation)
		inv.rsvp_status = doc.rsvp_status
		inv.response_date = doc.response_date
		inv.number_of_attendees = doc.number_of_attendees
		inv.save(ignore_permissions=True)


@frappe.whitelist()
def get_list(event, filters=None, limit=50, offset=0):
	"""Get RSVPs for an event."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = {"event": event}
	if filters:
		base_filters.update(filters)

	rsvps = frappe.get_list("RSVP",
		filters=base_filters,
		fields=["name", "guest", "guest_name", "invitation", "rsvp_status", "response_date",
			"number_of_attendees", "message", "responded_via"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="response_date DESC",
	)

	total = frappe.db.count("RSVP", base_filters)

	return {"rsvps": rsvps, "total": total}


@frappe.whitelist(allow_guest=True)
def submit_rsvp():
	"""Handle public RSVP submission."""
	return frappe.get_attr("invite.invite.doctype.rsvp.rsvp.public_rsvp")()
