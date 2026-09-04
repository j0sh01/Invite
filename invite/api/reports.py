# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import today, getdate


@frappe.whitelist()
def event_summary(event, **kwargs):
	"""Get a comprehensive summary report for an event."""
	event_doc = frappe.get_doc("Event", event)

	# Guest breakdown by category
	# (Raw SQL: frappe.get_all no longer accepts aggregate expressions like
	# "count(name) as count" in fields on newer Frappe versions.)
	guests_by_category = frappe.db.sql(
		"""
		SELECT category, COUNT(name) AS count
		FROM `tabGuest`
		WHERE event = %s
		GROUP BY category
		""",
		event,
		as_dict=True,
	)

	# RSVP breakdown
	rsvp_by_status = frappe.db.sql(
		"""
		SELECT rsvp_status, COUNT(name) AS count, SUM(number_of_attendees) AS attendees
		FROM `tabRSVP`
		WHERE event = %s
		GROUP BY rsvp_status
		""",
		event,
		as_dict=True,
	)

	# Check-in stats
	checkin_stats = frappe.db.sql(
		"""
		SELECT COUNT(name) AS total, SUM(is_duplicate) AS duplicates
		FROM `tabCheck-In`
		WHERE event = %s
		""",
		event,
		as_dict=True,
	)[0]

	return {
		"event": {
			"name": event_doc.name,
			"event_name": event_doc.event_name,
			"event_type": event_doc.event_type,
			"event_date": str(event_doc.event_date) if event_doc.event_date else None,
			"venue": event_doc.venue,
			"status": event_doc.event_status,
		},
		"guests_by_category": guests_by_category or [],
		"rsvp_by_status": rsvp_by_status or [],
		"checkins": {
			"total": checkin_stats.total or 0,
			"duplicates": checkin_stats.duplicates or 0,
		},
	}


@frappe.whitelist()
def guest_list(event, **kwargs):
	"""Get full guest list with all details for export."""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event},
		fields=["full_name", "email", "mobile_no", "category",
				"rsvp_status", "number_of_attendees", "invitation_status",
				"checked_in", "checked_in_at"],
		order_by="creation ASC",
	)
	return guests


@frappe.whitelist()
def dashboard(**kwargs):
	"""Get organizer dashboard data across all events."""
	events = frappe.get_all(
		"Event",
		fields=["name", "event_name", "event_type", "event_date", "event_status",
				"total_guests", "total_accepted", "total_checked_in"],
		order_by="event_date DESC",
		limit=10,
	)

	total_events = len(events)
	upcoming = len([e for e in events if e.event_date and getdate(e.event_date) >= getdate(today())])
	completed = len([e for e in events if e.event_status == "Completed"])

	total_guests = sum(e.total_guests or 0 for e in events)
	total_checked_in = sum(e.total_checked_in or 0 for e in events)

	return {
		"events": events,
		"stats": {
			"total_events": total_events,
			"upcoming": upcoming,
			"completed": completed,
			"total_guests": total_guests,
			"total_checked_in": total_checked_in,
		},
	}
