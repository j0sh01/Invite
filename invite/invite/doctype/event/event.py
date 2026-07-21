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
		self.set_public_rsvp_code()


	# Google Calendar integration hooks (suppressed)
	def sync_with_google_calendar(self):
		pass

	def pulled_from_google_calendar(self):
		return False

	def before_google_calendar_sync(self):
		pass

	def after_google_calendar_sync(self):
		pass

	def validate_dates(self):
		if self.event_date and getdate(self.event_date) < getdate(today()):
			frappe.throw("Event date cannot be in the past.")

		if self.end_date and self.event_date and getdate(self.end_date) < getdate(self.event_date):
			frappe.throw("End date cannot be before event date.")

	def set_public_rsvp_code(self):
		if self.enable_public_rsvp and not self.public_rsvp_code:
			import secrets
			self.public_rsvp_code = secrets.token_hex(6).upper()

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

		contributions = frappe.get_all(
			"Contribution",
			filters={"event": self.name},
			fields=["paid_amount", "name"],
		)
		self.total_contributions = len(contributions)
		self.total_contribution_amount = sum(c.paid_amount or 0 for c in contributions)

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
		"total_contributions": event.total_contributions,
		"total_contribution_amount": event.total_contribution_amount,
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
