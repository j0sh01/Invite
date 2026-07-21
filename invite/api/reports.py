# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import today, getdate, add_days


@frappe.whitelist()
def event_summary(event, **kwargs):
	"""Get a comprehensive summary report for an event."""
	event_doc = frappe.get_doc("Event", event)

	# Guest breakdown by category
	guests_by_category = frappe.get_all(
		"Guest",
		filters={"event": event},
		fields=["category", "count(name) as count"],
		group_by="category",
	)

	# RSVP breakdown
	rsvp_by_status = frappe.get_all(
		"RSVP",
		filters={"event": event},
		fields=["rsvp_status", "count(name) as count", "sum(number_of_attendees) as attendees"],
		group_by="rsvp_status",
	)

	# Contribution summary
	contribution_summary = frappe.get_all(
		"Contribution",
		filters={"event": event},
		fields=[
			"sum(pledged_amount) as total_pledged",
			"sum(paid_amount) as total_paid",
			"sum(outstanding_amount) as total_outstanding",
			"count(name) as total_contributions",
		],
	)[0]

	# Check-in stats
	checkin_stats = frappe.get_all(
		"Check-In",
		filters={"event": event},
		fields=["count(name) as total", "sum(is_duplicate) as duplicates"],
	)[0]

	# Top contributors
	top_contributors = frappe.get_all(
		"Contribution",
		filters={"event": event},
		fields=["guest", "guest_name", "sum(paid_amount) as total_paid"],
		group_by="guest",
		order_by="total_paid DESC",
		limit=10,
	)

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
		"contributions": {
			"total_pledged": contribution_summary.total_pledged or 0,
			"total_paid": contribution_summary.total_paid or 0,
			"total_outstanding": contribution_summary.total_outstanding or 0,
			"total_count": contribution_summary.total_contributions or 0,
		},
		"checkins": {
			"total": checkin_stats.total or 0,
			"duplicates": checkin_stats.duplicates or 0,
		},
		"top_contributors": top_contributors or [],
	}


@frappe.whitelist()
def guest_list(event, **kwargs):
	"""Get full guest list with all details for export."""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event},
		fields=["full_name", "email", "mobile_no", "category", "guest_type",
				"rsvp_status", "number_of_attendees", "invitation_status",
				"pledge_amount", "paid_amount", "outstanding_amount",
				"checked_in", "checked_in_at", "notes"],
		order_by="creation ASC",
	)
	return guests


@frappe.whitelist()
def dashboard(**kwargs):
	"""Get organizer dashboard data across all events."""
	events = frappe.get_all(
		"Event",
		fields=["name", "event_name", "event_type", "event_date", "event_status",
				"total_guests", "total_accepted", "total_checked_in",
				"total_contributions", "total_contribution_amount"],
		order_by="event_date DESC",
		limit=10,
	)

	total_events = len(events)
	upcoming = len([e for e in events if e.event_date and getdate(e.event_date) >= getdate(today())])
	completed = len([e for e in events if e.event_status == "Completed"])

	total_guests = sum(e.total_guests or 0 for e in events)
	total_checked_in = sum(e.total_checked_in or 0 for e in events)
	total_contributions = sum(e.total_contribution_amount or 0 for e in events)

	return {
		"events": events,
		"stats": {
			"total_events": total_events,
			"upcoming": upcoming,
			"completed": completed,
			"total_guests": total_guests,
			"total_checked_in": total_checked_in,
			"total_contributions": total_contributions,
		},
	}


@frappe.whitelist()
def financial_report(event, **kwargs):
	"""Get detailed financial report for an event."""
	contributions = frappe.get_all(
		"Contribution",
		filters={"event": event},
		fields=["guest_name", "contribution_type", "type", "pledged_amount",
				"paid_amount", "outstanding_amount", "payment_status",
				"payment_method", "payment_date", "transaction_reference"],
		order_by="creation DESC",
	)

	summary = frappe.get_all(
		"Contribution",
		filters={"event": event},
		fields=[
			"contribution_type",
			"count(name) as count",
			"sum(pledged_amount) as total_pledged",
			"sum(paid_amount) as total_paid",
		],
		group_by="contribution_type",
	)

	total_pledged = sum(c.pledged_amount or 0 for c in contributions)
	total_paid = sum(c.paid_amount or 0 for c in contributions)
	collection_rate = round(total_paid / total_pledged * 100, 1) if total_pledged > 0 else 0

	return {
		"contributions": contributions,
		"by_type": summary,
		"total_pledged": total_pledged,
		"total_paid": total_paid,
		"outstanding": total_pledged - total_paid,
		"collection_rate": collection_rate,
	}
