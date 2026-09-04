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
		self.persist_statistics()

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

	def persist_statistics(self):
		"""Write the computed statistics to the database.

		`on_update` runs after the document is already saved, so plain
		attribute changes would be lost. Persist them explicitly so the
		event header and dashboard always reflect live activity.
		"""
		stat_fields = [
			"total_guests",
			"total_invited",
			"total_rsvped",
			"total_accepted",
			"total_declined",
			"total_checked_in",
		]
		self.db_set({field: getattr(self, field, 0) for field in stat_fields}, update_modified=False)

	def auto_update_status(self, target_status):
		"""Advance the event status forward based on system activity.

		Rules:
		- Forward-only: never downgrades to an earlier milestone.
		- 'Cancelled' is manual-only and is never touched.
		- 'Completed' is never auto-overridden.
		- Manual changes are respected; auto logic only advances ahead.

		Milestones are ordered by the 'position' field on Event Status.
		"""
		if self.event_status == "Cancelled":
			return
		if self.event_status == "Completed":
			return

		current_position = self._status_position(self.event_status)
		target_position = self._status_position(target_status)
		if current_position is None or target_position is None:
			return
		if target_position <= current_position:
			return

		self.db_set("event_status", target_status, update_modified=False)

	@staticmethod
	def _status_position(status):
		return frappe.db.get_value("Event Status", status, "position")


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
