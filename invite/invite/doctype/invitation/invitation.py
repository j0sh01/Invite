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
	"""Send bulk invitations for an event."""
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

	for inv_name in invitations:
		try:
			inv = frappe.get_doc("Invitation", inv_name)
			inv.delivery_method = invitation_type
			inv.status = "Sent"
			inv.sent_at = now()
			inv.delivery_status = "Sent"
			inv.save(ignore_permissions=True)
			sent.append(inv_name)
		except Exception as e:
			failed.append({"invitation": inv_name, "error": str(e)})

	return {"sent": sent, "failed": failed, "total": len(invitations)}


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

	return {"qr_code_url": f"/files/{filename}", "invite_code": inv.invite_code}
