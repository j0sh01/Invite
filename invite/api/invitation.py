# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe


def before_insert(doc, method=None):
	if not doc.invite_code:
		import secrets
		doc.invite_code = secrets.token_hex(8).upper()

	if not doc.qr_code and doc.invite_code:
		from frappe.utils import get_url
		doc.qr_code = f"{get_url()}/api/method/invite.api.check_in.scan_qr?code={doc.invite_code}&event={doc.event}"


def after_insert(doc, method=None):
	if doc.guest:
		guest_status_map = {
			"Draft": "Not Sent", "Ready": "Not Sent", "Sent": "Sent",
			"Delivered": "Delivered", "Failed": "Failed", "Cancelled": "Not Sent",
		}
		frappe.db.set_value("Guest", doc.guest, {
			"invitation_status": guest_status_map.get(doc.status, "Not Sent"),
			"invite_code": doc.invite_code,
			"qr_code": doc.qr_code,
		})


@frappe.whitelist()
def get_list(event, filters=None, limit=50, offset=0):
	"""Get invitations for an event."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = {"event": event}
	if filters:
		base_filters.update(filters)

	invitations = frappe.get_list("Invitation",
		filters=base_filters,
		fields=["name", "guest", "guest_name", "invite_code", "invitation_type", "status",
			"delivery_method", "sent_at", "delivery_status", "rsvp_status", "response_date",
			"qr_code_image", "personalized_invite_card"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="creation DESC",
	)

	total = frappe.db.count("Invitation", base_filters)

	return {"invitations": invitations, "total": total}


@frappe.whitelist()
def create_invitations(event, guest_ids, invitation_type="Digital", delivery_method="WhatsApp"):
	"""Create invitations for multiple guests."""
	if isinstance(guest_ids, str):
		guest_ids = json.loads(guest_ids)

	created = []
	errors = []

	for guest_id in guest_ids:
		try:
			existing = frappe.db.get_value("Invitation", {"event": event, "guest": guest_id}, "name")
			if existing:
				errors.append({"guest": guest_id, "error": "Invitation already exists"})
				continue

			guest = frappe.get_cached_doc("Guest", guest_id)
			inv = frappe.new_doc("Invitation")
			inv.event = event
			inv.guest = guest_id
			inv.guest_name = guest.full_name
			inv.invitation_type = invitation_type
			inv.delivery_method = delivery_method
			inv.status = "Ready"
			inv.insert(ignore_permissions=True)
			created.append(inv.name)
		except Exception as e:
			errors.append({"guest": guest_id, "error": str(e)})

	return {"created": created, "errors": errors, "total_created": len(created), "total_errors": len(errors)}


@frappe.whitelist()
def send(event, invitation_type="WhatsApp"):
	"""Send pending invitations."""
	return frappe.get_attr("invite.invite.doctype.invitation.invitation.send_invitations")(event, invitation_type)


@frappe.whitelist()
def generate_qr(invitation):
	"""Generate QR code for an invitation."""
	return frappe.get_attr("invite.invite.doctype.invitation.invitation.generate_qr_code")(invitation)
