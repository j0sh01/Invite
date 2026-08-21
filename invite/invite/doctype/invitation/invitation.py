# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, get_url


class Invitation(Document):
	def before_validate(self):
		self.set_invite_code()
		self.set_qr_code_data()

	def validate(self):
		if not self.guest_name and self.guest:
			guest = frappe.get_cached_doc("Guest", self.guest)
			self.guest_name = guest.full_name

	def set_invite_code(self):
		if not self.invite_code:
			import secrets
			self.invite_code = secrets.token_hex(8).upper()

	def set_qr_code_data(self):
		"""Generate QR code data with event and guest info."""
		if self.invite_code and not self.qr_code:
			base_url = get_url()
			qr_data = f"{base_url}/api/method/invite.api.check_in.scan_qr?code={self.invite_code}&event={self.event}"
			self.qr_code = qr_data

	def on_update(self):
		self.update_guest_invitation_status()

	def update_guest_invitation_status(self):
		"""Sync invitation status back to guest."""
		if self.guest:
			guest = frappe.get_doc("Guest", self.guest)
			guest.invitation_status = self.status
			guest.invite_code = self.invite_code
			guest.qr_code = self.qr_code_image or guest.qr_code
			if self.status in ["Sent", "Delivered"]:
				guest.invitation_sent_on = self.sent_at or now()
			# Update RSVP status from invitation
			if self.rsvp_status:
				guest.rsvp_status = self.rsvp_status
			guest.save(ignore_permissions=True)


@frappe.whitelist()
def send_invitations(event, invitation_type="WhatsApp"):
	"""Send bulk invitations for an event via WhatsApp/Twilio.

	Actually dispatches messages through the configured provider.
	For Twilio, uses Content API templates if SIDs are configured.
	Falls back to plain text if no template is available.
	"""
	invitations = frappe.get_all(
		"Invitation",
		filters={
			"event": event,
			"status": ["in", ["Draft", "Ready"]],
		},
		pluck="name",
	)

	sent = []
	failed = []
	settings = frappe.get_single("Event Settings")
	provider = getattr(settings, "whatsapp_provider", "")

	for inv_name in invitations:
		try:
			inv = frappe.get_doc("Invitation", inv_name)
			inv.delivery_method = invitation_type

			# Actually send the message
			if provider == "Twilio" and invitation_type == "WhatsApp":
				success = _send_twilio_invitation(inv, settings, event)
			elif provider == "Official WhatsApp API" and invitation_type == "WhatsApp":
				success = _send_meta_api_invitation(inv, settings, event)
			else:
				success = True  # Non-WhatsApp delivery methods (Email/SMS/Manual)

			if success:
				inv.status = "Sent"
				inv.sent_at = now()
				inv.delivery_status = "Sent"
			else:
				inv.status = "Failed"
				inv.delivery_status = "Failed"
				inv.delivery_error = "Failed to send via configured provider"

			inv.save(ignore_permissions=True)
			sent.append(inv_name)
		except Exception as e:
			try:
				inv = frappe.get_doc("Invitation", inv_name)
				inv.status = "Failed"
				inv.delivery_status = "Failed"
				inv.delivery_error = str(e)[:500]
				inv.save(ignore_permissions=True)
			except Exception:
				pass
			failed.append({"invitation": inv_name, "error": str(e)})

	# Audit log
	if sent:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=event,
				action_type="Invitation Sent",
				subject=f"{len(sent)} invitation(s) sent via {invitation_type}",
				extra_data={"sent": sent[:10], "failed_count": len(failed), "delivery_method": invitation_type},
			)
		except Exception:
			pass

	if failed:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=event,
				action_type="Invitation Failed",
				subject=f"{len(failed)} invitation(s) failed to send",
				extra_data={"failed": failed[:10], "delivery_method": invitation_type},
			)
		except Exception:
			pass

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total": len(invitations)}


def _send_twilio_invitation(inv, settings, event_name):
	"""Send a single invitation via Twilio Content API.

	Uses the configured Content SID template. Falls back to plain text
	if no template SID is configured.
	"""
	from invite.api.twilio import send_template_message, send_whatsapp_message, get_template_sids

	contact = inv.recipient_contact or ""
	if not contact and inv.guest:
		guest = frappe.get_cached_doc("Guest", inv.guest)
		contact = guest.mobile_no or ""

	if not contact:
		return False

	# Get template SID for event invitation
	tids = get_template_sids()
	template_sid = tids.get("event_invitation", "")

	if template_sid:
		# Build template variables
		base_url = frappe.utils.get_url()
		rsvp_link = f"{base_url}/rsvp?code={inv.invite_code}"
		event_doc = frappe.get_doc("Event", event_name)
		variables = {
			"1": inv.guest_name or "Guest",
			"2": event_doc.event_name or "Event",
			"3": str(event_doc.event_date or ""),
			"4": event_doc.event_time or "",
			"5": event_doc.venue or "",
			"6": rsvp_link,
		}
		return send_template_message(contact, template_sid, variables)
	else:
		# Fallback: send plain text
		base_url = frappe.utils.get_url()
		rsvp_link = f"{base_url}/rsvp?code={inv.invite_code}"
		event_doc = frappe.get_doc("Event", event_name)
		message = (
			f"Dear {inv.guest_name or 'Guest'}, you are invited to "
			f"{event_doc.event_name} on {event_doc.event_date} at {event_doc.venue}.\n\n"
			f"Please RSVP here: {rsvp_link}"
		)
		return send_whatsapp_message(contact, message)


def _send_meta_api_invitation(inv, settings, event_name):
	"""Send a single invitation via Meta WhatsApp Cloud API."""
	from invite.api.whatsapp import send_text_message

	contact = inv.recipient_contact or ""
	if not contact and inv.guest:
		guest = frappe.get_cached_doc("Guest", inv.guest)
		contact = guest.mobile_no or ""

	if not contact:
		return False

	base_url = frappe.utils.get_url()
	rsvp_link = f"{base_url}/rsvp?code={inv.invite_code}"
	event_doc = frappe.get_doc("Event", event_name)
	message = (
			f"Dear {inv.guest_name or 'Guest'}, you are invited to "
			f"{event_doc.event_name} on {event_doc.event_date} at {event_doc.venue}.\n\n"
			f"Please RSVP here: {rsvp_link}"
		)

	return send_text_message(contact, message)


@frappe.whitelist()
def send_single_invitation(invitation, delivery_method="WhatsApp"):
	"""Send a single invitation via WhatsApp/Twilio.

	Works for both fresh sends and retries of failed invitations.
	Clears any previous error before attempting to send.
	"""
	inv = frappe.get_doc("Invitation", invitation)
	settings = frappe.get_single("Event Settings")
	provider = getattr(settings, "whatsapp_provider", "")

	inv.delivery_method = delivery_method

	# Clear old error on retry
	if inv.status == "Failed":
		inv.delivery_error = ""
		inv.status = "Ready"

	try:
		if provider == "Twilio" and delivery_method == "WhatsApp":
			success = _send_twilio_invitation(inv, settings, inv.event)
		elif provider == "Official WhatsApp API" and delivery_method == "WhatsApp":
			success = _send_meta_api_invitation(inv, settings, inv.event)
		else:
			success = True  # Non-WhatsApp delivery methods

		if success:
			inv.status = "Sent"
			inv.sent_at = now()
			inv.delivery_status = "Sent"
			inv.delivery_error = ""
		else:
			inv.status = "Failed"
			inv.delivery_status = "Failed"
			inv.delivery_error = "Failed to send via configured provider"

		inv.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": success,
			"message": f"Invitation sent to {inv.guest_name}" if success else f"Failed to send to {inv.guest_name}",
			"invitation": inv.name,
		}

	except Exception as e:
		inv.status = "Failed"
		inv.delivery_status = "Failed"
		inv.delivery_error = str(e)[:500]
		inv.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": False,
			"message": str(e),
			"invitation": inv.name,
		}


@frappe.whitelist()
def generate_qr_code(invitation):
	"""Generate QR code image for an invitation."""
	import io
	import qrcode
	from frappe.utils import get_site_path
	import os

	inv = frappe.get_doc("Invitation", invitation)
	if not inv.qr_code:
		inv.set_qr_code_data()
		inv.save(ignore_permissions=True)

	# Generate QR code image
	qr = qrcode.QRCode(version=1, box_size=8, border=2)
	qr.add_data(inv.qr_code)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")

	# Save to file
	filename = f"qr_{inv.invite_code}.png"
	path = os.path.join(get_site_path("public", "files"), filename)
	img.save(path)

	# Attach to invitation
	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_url": f"/files/{filename}",
		"attached_to_doctype": "Invitation",
		"attached_to_name": invitation,
		"is_private": 0,
	})
	file_doc.insert(ignore_permissions=True)

	inv.db_set("qr_code_image", f"/files/{filename}")

	# Audit log
	try:
		from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
		log_action(
			event=inv.event,
			action_type="QR Code Generated",
			subject=f"QR code generated for {inv.guest_name}",
			guest=inv.guest,
			guest_name=inv.guest_name,
			reference_doctype="Invitation",
			reference_name=inv.name,
		)
	except Exception:
		pass

	return {"qr_code_url": f"/files/{filename}", "invite_code": inv.invite_code}
