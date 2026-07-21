# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class CheckIn(Document):
	def validate(self):
		if not self.checked_in_at:
			self.checked_in_at = now()
		if not self.checked_in_by:
			self.checked_in_by = frappe.session.user
		self.set_number_of_attendees()
		self.detect_duplicate()
		if not self.is_duplicate:
			self.update_guest_checkin()

	def set_number_of_attendees(self):
		"""Set the number of attendees based on guest type."""
		if self.guest and not self.number_of_attendees:
			guest = frappe.get_cached_doc("Guest", self.guest)
			self.number_of_attendees = guest.number_of_attendees or 1

	def get_allowed_scans(self):
		"""Get how many check-in scans are allowed for this guest based on type."""
		if not self.guest:
			return 1
		guest = frappe.get_cached_doc("Guest", self.guest)
		# Couple/Family can have multiple scans; Individual/Group = 1
		guest_type_map = {
			"Individual": 1,
			"Couple": 2,
		}
		allowed = guest_type_map.get(guest.guest_type)
		if allowed is not None:
			return allowed
		# For Family/Group types, use number_of_attendees (default 1)
		return guest.number_of_attendees or 1

	def detect_duplicate(self):
		"""Check if guest has exceeded allowed check-in scans based on guest type.
		- Individual: max 1 scan before duplicate
		- Couple: max 2 scans before duplicate
		- Family/Group: max = number_of_attendees before duplicate
		"""
		if not self.guest:
			return

		allowed = self.get_allowed_scans()
		existing_count = frappe.db.count(
			"Check-In",
			{"guest": self.guest, "event": self.event, "is_duplicate": 0, "name": ["!=", self.name]},
		)
		if existing_count >= allowed:
			self.is_duplicate = 1

	def update_guest_checkin(self):
		"""Update guest record with check-in info (only for non-duplicate scans)."""
		if self.guest:
			guest = frappe.get_doc("Guest", self.guest)
			guest.checked_in = 1
			guest.checked_in_at = self.checked_in_at or now()
			guest.checked_in_by = self.checked_in_by
			guest.save(ignore_permissions=True)


@frappe.whitelist()
def scan_qr():
	"""Handle QR code scan for check-in."""
	code = frappe.local.form_dict.get("code")
	event = frappe.local.form_dict.get("event")

	if not code or not event:
		frappe.throw("Invalid QR code data.")

	# Find the invitation by invite code
	invitation = frappe.db.get_value(
		"Invitation",
		{"invite_code": code, "event": event},
		["name", "guest", "guest_name"],
		as_dict=True,
	)

	if not invitation:
		# Try finding guest directly
		guest = frappe.db.get_value(
			"Guest",
			{"invite_code": code, "event": event},
			["name", "full_name"],
			as_dict=True,
		)
		if not guest:
			frappe.throw("Invalid or expired invitation code.")

		invitation = {"name": None, "guest": guest.name, "guest_name": guest.full_name}

	# Create check-in record
	checkin = frappe.new_doc("Check-In")
	checkin.event = event
	checkin.guest = invitation.guest
	checkin.guest_name = invitation.guest_name
	checkin.invitation = invitation.name
	checkin.check_in_method = "QR Code Scan"
	checkin.insert(ignore_permissions=True)

	return {
		"success": True,
		"guest_name": invitation.guest_name,
		"checked_in_at": str(checkin.checked_in_at),
		"is_duplicate": checkin.is_duplicate,
		"number_of_attendees": checkin.number_of_attendees,
	}


@frappe.whitelist()
def manual_checkin(event, guest=None, invite_code=None):
	"""Manual check-in by guest name or invite code."""
	if not guest and not invite_code:
		frappe.throw("Please provide a guest name or invite code.")

	if invite_code:
		guest_doc = frappe.db.get_value(
			"Guest",
			{"invite_code": invite_code, "event": event},
			["name", "full_name"],
			as_dict=True,
		)
	else:
		guest_doc = frappe.db.get_value(
			"Guest",
			{"name": guest, "event": event},
			["name", "full_name"],
			as_dict=True,
		)

	if not guest_doc:
		frappe.throw("Guest not found.")

	invitation = frappe.db.get_value(
		"Invitation",
		{"guest": guest_doc.name, "event": event},
		"name",
	)

	checkin = frappe.new_doc("Check-In")
	checkin.event = event
	checkin.guest = guest_doc.name
	checkin.guest_name = guest_doc.full_name
	checkin.invitation = invitation
	checkin.check_in_method = "Manual Entry" if guest else "Invite Code"
	checkin.insert(ignore_permissions=True)

	return {
		"success": True,
		"guest_name": guest_doc.full_name,
		"checked_in_at": str(checkin.checked_in_at),
		"is_duplicate": checkin.is_duplicate,
		"number_of_attendees": checkin.number_of_attendees,
	}


@frappe.whitelist()
def get_checkin_stats(event):
	"""Get check-in statistics for an event."""
	checkins = frappe.get_all(
		"Check-In",
		filters={"event": event},
		fields=["name", "is_duplicate"],
	)

	total_checkins = len(checkins)
	total_duplicates = len([c for c in checkins if c.is_duplicate])

	total_guests = frappe.db.count("Guest", {"event": event})
	total_rsvp_accepted = frappe.db.count(
		"RSVP",
		{"event": event, "rsvp_status": "Accepted"},
	)

	return {
		"total_guests": total_guests,
		"total_checkins": total_checkins,
		"total_duplicates": total_duplicates,
		"unique_checkins": total_checkins - total_duplicates,
		"rsvp_accepted": total_rsvp_accepted,
		"checkin_rate": round((total_checkins - total_duplicates) / total_guests * 100, 1) if total_guests > 0 else 0,
	}
