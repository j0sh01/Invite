# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now, getdate


class Event(Document):
	def before_validate(self):
		if not self.event_status:
			self.event_status = "Planning"
		if not self.currency:
			settings = frappe.get_single("Event Settings")
			self.currency = settings.default_currency or "TZS"

	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if self.event_date and getdate(self.event_date) < getdate(today()):
			frappe.throw("Event date cannot be in the past.")

	def on_update(self):
		self.update_statistics()

	def update_statistics(self):
		"""Update event statistics from related documents."""
		guests = frappe.get_all("Guest", filters={"event": self.name}, pluck="name")
		self.total_guests = len(guests)

		invitations = frappe.get_all(
			"Invitation",
			filters={"event": self.name, "status": ["in", ["Sent", "Delivered"]]},
			pluck="name",
		)
		self.total_invited = len(invitations)

		rsvps = frappe.get_all(
			"RSVP",
			filters={"event": self.name},
			fields=["rsvp_status", "name"],
		)
		self.total_rsvped = len(rsvps)
		self.total_accepted = len([r for r in rsvps if r.rsvp_status == "Accepted"])
		self.total_declined = len([r for r in rsvps if r.rsvp_status == "Declined"])

		checkins = frappe.get_all(
			"Check-In",
			filters={"event": self.name},
			pluck="name",
		)
		self.total_checked_in = len(checkins)


@frappe.whitelist()
def get_event_stats(event_name, **kwargs):
	"""Get comprehensive statistics for an event."""
	event = frappe.get_doc("Event", event_name)
	return {
		"total_guests": event.total_guests,
		"total_invited": event.total_invited,
		"total_rsvped": event.total_rsvped,
		"total_accepted": event.total_accepted,
		"total_declined": event.total_declined,
		"total_checked_in": event.total_checked_in,
	}


@frappe.whitelist()
def get_upcoming_events(**kwargs):
	"""Get upcoming events for the dashboard."""
	return frappe.get_all(
		"Event",
		filters={
			"event_date": [">=", today()],
			"event_status": ["!=", "Cancelled"],
		},
		fields=["name", "event_name", "event_type", "event_date", "event_time", "venue", "event_status", "total_guests", "total_accepted", "total_checked_in"],
		order_by="event_date ASC",
	)
