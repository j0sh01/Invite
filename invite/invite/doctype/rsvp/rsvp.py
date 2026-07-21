# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class RSVP(Document):
	def validate(self):
		if not self.response_date:
			self.response_date = now()
		self.link_to_guest()

	def link_to_guest(self):
		"""Sync RSVP status back to guest and invitation."""
		if self.guest:
			guest = frappe.get_doc("Guest", self.guest)
			guest.rsvp_status = self.rsvp_status
			guest.rsvp_date = self.response_date
			if self.number_of_attendees:
				guest.number_of_attendees = self.number_of_attendees
			guest.save(ignore_permissions=True)

		if self.invitation:
			inv = frappe.get_doc("Invitation", self.invitation)
			inv.rsvp_status = self.rsvp_status
			inv.response_date = self.response_date
			inv.number_of_attendees = self.number_of_attendees
			inv.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def public_rsvp():
	"""Handle public RSVP submission from invitation link."""
	args = frappe.local.form_dict

	invite_code = args.get("code")
	if not invite_code:
		frappe.throw("Invalid invitation code.")

	invitation = frappe.get_doc("Invitation", {"invite_code": invite_code})
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
	rsvp.rsvp_status = args.get("status", "Accepted")
	rsvp.number_of_attendees = int(args.get("attendees", 1))
	rsvp.message = args.get("message", "")
	rsvp.responded_via = "Web"

	if existing:
		rsvp.save(ignore_permissions=True)
	else:
		rsvp.insert(ignore_permissions=True)

	return {"success": True, "message": "RSVP submitted successfully."}


@frappe.whitelist()
def get_rsvp_summary(event):
	"""Get RSVP summary for an event."""
	rsvps = frappe.get_all(
		"RSVP",
		filters={"event": event},
		fields=["rsvp_status", "number_of_attendees"],
	)

	total = len(rsvps)
	accepted = len([r for r in rsvps if r.rsvp_status == "Accepted"])
	declined = len([r for r in rsvps if r.rsvp_status == "Declined"])
	pending = len([r for r in rsvps if r.rsvp_status == "Pending"])
	maybe = len([r for r in rsvps if r.rsvp_status == "Maybe"])
	total_attendees = sum(r.number_of_attendees or 1 for r in rsvps if r.rsvp_status in ["Accepted", "Maybe"])

	return {
		"total": total,
		"accepted": accepted,
		"declined": declined,
		"pending": pending,
		"maybe": maybe,
		"total_attendees": total_attendees,
	}
