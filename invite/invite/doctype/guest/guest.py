# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class Guest(Document):
	def before_validate(self):
		self.set_full_name()
		self.set_invite_code()

	def validate(self):
		self.validate_duplicate()

	def set_full_name(self):
		parts = [self.first_name, self.last_name]
		self.full_name = " ".join(filter(None, parts))

	def set_invite_code(self):
		if not self.invite_code:
			import secrets
			self.invite_code = secrets.token_hex(8).upper()

	def validate_duplicate(self):
		"""Check for duplicate guests in the same event."""
		if self.email:
			existing = frappe.db.get_value(
				"Guest",
				{"event": self.event, "email": self.email, "name": ["!=", self.name]},
				"name",
			)
			if existing:
				frappe.throw(f"A guest with email {self.email} already exists in this event.")

		if self.mobile_no:
			existing = frappe.db.get_value(
				"Guest",
				{"event": self.event, "mobile_no": self.mobile_no, "name": ["!=", self.name]},
				"name",
			)
			if existing:
				frappe.throw(f"A guest with mobile number {self.mobile_no} already exists in this event.")

	def on_update(self):
		self.sync_unsent_invitation_contacts()
		self.sync_invitation_attendees()
		self.update_event_stats()

	def sync_invitation_attendees(self):
		"""Mirror the guest's card coverage onto their invitation(s).

		number_of_attendees on the Guest is the source of truth (the check-in
		scanner allows that many scans per card), so whenever it changes the
		Invitation record is updated too - otherwise the Invitations tab keeps
		showing a stale count for that guest (e.g. 1) while the Guests tab says
		the card covers 2+ people.
		"""
		before = self.get_doc_before_save()
		if before is not None and (before.number_of_attendees or 1) == (self.number_of_attendees or 1):
			return

		frappe.db.set_value(
			"Invitation",
			{"guest": self.name, "event": self.event},
			"number_of_attendees",
			self.number_of_attendees or 1,
			update_modified=False,
		)

	def sync_unsent_invitation_contacts(self):
		"""When a guest's mobile number changes, point every invitation that has
		not been delivered yet (Draft/Ready/Failed) at the new number, so retries
		and pending sends reach the corrected number instead of the old one."""
		if not self.mobile_no:
			return

		before = self.get_doc_before_save()
		if before and before.mobile_no == self.mobile_no:
			return

		frappe.db.set_value(
			"Invitation",
			{
				"guest": self.name,
				"status": ["in", ["Draft", "Ready", "Failed"]],
			},
			"recipient_contact",
			self.mobile_no,
			update_modified=False,
		)

	def update_event_stats(self):
		event = frappe.get_doc("Event", self.event)
		event.update_statistics()
		event.save(ignore_permissions=True)


@frappe.whitelist()
def import_guests(event, guests_data, **kwargs):
	"""Bulk import guests from JSON data."""
	import json

	if isinstance(guests_data, str):
		guests_data = json.loads(guests_data)

	created = []
	errors = []

	for idx, guest_data in enumerate(guests_data):
		try:
			guest = frappe.new_doc("Guest")
			guest.event = event
			guest.first_name = guest_data.get("first_name")
			guest.last_name = guest_data.get("last_name", "")
			guest.email = guest_data.get("email", "")
			guest.mobile_no = guest_data.get("mobile_no", "")
			guest.phone = guest_data.get("phone", "")
			guest.category = guest_data.get("category", "")
			guest.number_of_attendees = guest_data.get("number_of_attendees", 1)
			guest.plus_one = guest_data.get("plus_one", 0)
			guest.plus_one_name = guest_data.get("plus_one_name", "")
			guest.insert(ignore_permissions=True)
			created.append(guest.name)
		except Exception as e:
			errors.append({"row": idx + 1, "error": str(e)})

	return {"created": created, "errors": errors, "total": len(guests_data)}


@frappe.whitelist()
def get_event_guests(event, **kwargs):
	"""Get all guests for an event with summary."""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event},
		fields=["name", "full_name", "email", "mobile_no", "category", "rsvp_status",
				"checked_in", "invitation_status", "number_of_attendees"],
		order_by="creation ASC",
	)

	# Per-guest scan progress: how many of their allowed scans have been used
	# (number_of_attendees = how many people the card covers, i.e. how many
	# times it may be scanned — 1 for single, 2 for double entry, etc.)
	counts = dict(
		frappe.db.get_all(
			"Check-In",
			filters={"event": event, "is_duplicate": 0},
			fields=["guest", "count(*) as total"],
			group_by="guest",
			as_list=True,
		)
	)
	for g in guests:
		g["scans_used"] = counts.get(g["name"], 0)
		g["scans_allowed"] = g.get("number_of_attendees") or 1

	return {
		"guests": guests,
		"total": len(guests),
		"checked_in": len([g for g in guests if g.checked_in]),
		"rsvped": len([g for g in guests if g.rsvp_status and g.rsvp_status != "Pending"]),
	}
