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
		fields=["name", "guest", "guest_name", "invite_code", "status",
			"delivery_method", "recipient_contact", "sent_at", "delivered_at",
			"delivery_status", "delivery_error", "viewed_at",
			"rsvp_status", "response_date", "number_of_attendees",
			"qr_code_image", "personalized_invite_card"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="creation DESC",
	)

	total = frappe.db.count("Invitation", base_filters)

	return {"invitations": invitations, "total": total}


@frappe.whitelist()
def create_invitations(event, guest_ids, delivery_method="WhatsApp"):
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
			inv.delivery_method = delivery_method
			inv.status = "Ready"
			inv.insert(ignore_permissions=True)
			created.append(inv.name)
		except Exception as e:
			errors.append({"guest": guest_id, "error": str(e)})

	# Audit log for bulk creation
	if created:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=event,
				action_type="Invitation Created",
				subject=f"{len(created)} invitation(s) created",
				extra_data={"created": created, "delivery_method": delivery_method},
			)
		except Exception:
			pass

	return {"created": created, "errors": errors, "total_created": len(created), "total_errors": len(errors)}


@frappe.whitelist()
def send(event, delivery_method="WhatsApp"):
	"""Send pending invitations."""
	return frappe.get_attr("invite.invite.doctype.invitation.invitation.send_invitations")(event, delivery_method)


@frappe.whitelist()
def generate_cards(event, guest_ids=None):
	"""Generate (or regenerate) the personalized invitation cards for an event.

	Every invitation gets a fresh card PDF built from the event's current
	template, photo and the guest's own QR code. Progress is streamed to the
	requesting user in realtime via the ``invite_card_progress`` socket event
	(after each card), so the UI can show a live progress view.

	Returns a summary of generated/failed cards.
	"""
	from invite.api.card import generate_invitation_card

	if isinstance(guest_ids, str):
		guest_ids = json.loads(guest_ids) if guest_ids else None

	event_doc = frappe.get_doc("Event", event)
	if not event_doc.image:
		frappe.throw(
			"Please upload an Event Image in Event Settings before generating invitation cards.",
			title="Event Image Required",
		)

	filters = {"event": event}
	if guest_ids:
		filters["guest"] = ["in", guest_ids]

	invitations = frappe.get_all(
		"Invitation",
		filters=filters,
		fields=["name", "guest_name", "invite_code"],
		order_by="creation ASC",
	)
	total = len(invitations)
	if not total:
		return {"generated": [], "failed": [], "total": 0, "generated_count": 0, "failed_count": 0}

	generated = []
	failed = []

	for idx, inv in enumerate(invitations, start=1):
		try:
			result = generate_invitation_card(inv.name)
			generated.append({
				"invitation": inv.name,
				"guest_name": inv.guest_name,
				"card_url": result.get("card_url", ""),
			})
			frappe.publish_realtime("invite_card_progress", {
				"index": idx,
				"total": total,
				"guest_name": inv.guest_name,
				"invite_code": inv.invite_code,
				"status": "done",
				"card_url": result.get("card_url", ""),
			}, user=frappe.session.user)
		except Exception as e:
			failed.append({"invitation": inv.name, "guest_name": inv.guest_name, "error": str(e)})
			frappe.publish_realtime("invite_card_progress", {
				"index": idx,
				"total": total,
				"guest_name": inv.guest_name,
				"invite_code": inv.invite_code,
				"status": "error",
				"error": str(e)[:300],
			}, user=frappe.session.user)
			frappe.log_error(
				f"Card generation failed for {inv.name} ({inv.guest_name}): {frappe.get_traceback()}",
				"Generate Cards",
			)
		frappe.db.commit()

	return {
		"generated": generated,
		"failed": failed,
		"total": total,
		"generated_count": len(generated),
		"failed_count": len(failed),
	}


@frappe.whitelist()
def generate_qr(invitation):
	"""Generate QR code for an invitation."""
	return frappe.get_attr("invite.invite.doctype.invitation.invitation.generate_qr_code")(invitation)
