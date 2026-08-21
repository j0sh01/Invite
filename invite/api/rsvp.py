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

	# Audit log
	try:
		from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
		guest_name = doc.guest_name or ""
		if not guest_name and doc.guest:
			guest_name = frappe.db.get_value("Guest", doc.guest, "full_name") or ""
		log_action(
			event=doc.event,
			action_type="RSVP Submitted",
			subject=f"{guest_name} RSVP: {doc.rsvp_status}",
			guest=doc.guest,
			guest_name=guest_name,
			reference_doctype="RSVP",
			reference_name=doc.name,
			extra_data={"status": doc.rsvp_status, "attendees": doc.number_of_attendees, "responded_via": doc.responded_via},
		)
	except Exception:
		pass


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
def get_invitation_by_code(code):
	"""Get invitation details by invite code for public RSVP page."""
	if not code:
		frappe.throw("Invalid invitation code.")

	invitation = frappe.db.get_value(
		"Invitation",
		{"invite_code": code},
		["name", "event", "guest", "guest_name", "invite_code", "status"],
		as_dict=True,
	)

	if not invitation:
		frappe.throw("Invitation not found.")

	event = frappe.db.get_value(
		"Event",
		invitation.event,
		["event_name", "event_date", "event_time", "venue", "location_address", "image", "enable_public_rsvp"],
		as_dict=True,
	)

	if not event or not event.enable_public_rsvp:
		frappe.throw("Public RSVP is not enabled for this event.")

	return {
		"invitation": {
			"name": invitation.name,
			"guest_name": invitation.guest_name,
			"invite_code": invitation.invite_code,
			"event_name": event.event_name,
			"event_date": str(event.event_date) if event.event_date else None,
			"event_time": event.event_time,
			"venue": event.venue,
			"location_address": event.location_address,
			"event_image": event.image,
			"status": invitation.status,
		}
	}


@frappe.whitelist(allow_guest=True)
def submit_rsvp(code=None, status="Accepted", attendees=1, message=""):
	"""Handle public RSVP submission."""
	if not code:
		frappe.throw("Invalid invitation code.")

	invitation = frappe.get_doc("Invitation", {"invite_code": code})
	if not invitation:
		frappe.throw("Invitation not found.")

	guest = frappe.get_doc("Guest", invitation.guest)

	# Create or update RSVP
	existing = frappe.db.get_value("RSVP", {"invitation": invitation.name, "guest": guest.name}, "name")
	if existing:
		rsvp = frappe.get_doc("RSVP", existing)
	else:
		rsvp = frappe.new_doc("RSVP")

	rsvp.event = invitation.event
	rsvp.guest = guest.name
	rsvp.invitation = invitation.name
	rsvp.rsvp_status = status
	rsvp.number_of_attendees = int(attendees)
	rsvp.message = message
	rsvp.responded_via = "Web"

	if existing:
		rsvp.save(ignore_permissions=True)
	else:
		rsvp.insert(ignore_permissions=True)

	return {"success": True, "message": "RSVP submitted successfully."}
