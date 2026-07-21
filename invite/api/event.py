# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe
from frappe.utils import today


@frappe.whitelist()
def get_list(filters=None, limit=20, offset=0):
	"""Get list of events."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = filters or {}

	events = frappe.get_list("Event",
		filters=base_filters,
		fields=["name", "event_name", "event_type", "event_date", "event_time", "venue",
			"event_status", "total_guests", "total_accepted", "total_checked_in",
			"total_contributions", "total_contribution_amount", "image"],
		limit_start=offset,
		limit_page_length=limit,
		order_by="event_date DESC",
	)

	total = frappe.db.count("Event", base_filters)

	return {"events": events, "total": total}


@frappe.whitelist()
def get(event):
	"""Get a single event with details."""
	event_doc = frappe.get_doc("Event", event)

	recent_checkins = frappe.get_all("Check-In",
		filters={"event": event},
		fields=["guest_name", "checked_in_at", "is_duplicate"],
		limit=10,
		order_by="checked_in_at DESC",
	)

	return {"event": event_doc, "recent_checkins": recent_checkins}


@frappe.whitelist()
def create(data):
	"""Create a new event."""
	if isinstance(data, str):
		data = json.loads(data)

	event = frappe.new_doc("Event")
	event.update(data)
	event.insert(ignore_permissions=True)

	return {"name": event.name, "event_name": event.event_name}


@frappe.whitelist()
def update(event, data):
	"""Update an event."""
	if isinstance(data, str):
		data = json.loads(data)

	event_doc = frappe.get_doc("Event", event)
	event_doc.update(data)
	event_doc.save(ignore_permissions=True)

	return {"name": event_doc.name, "event_name": event_doc.event_name}


@frappe.whitelist()
def delete(event):
	"""Delete an event."""
	frappe.delete_doc("Event", event)
	return {"success": True}


@frappe.whitelist()
def get_dashboard_stats():
	"""Get dashboard statistics."""
	total_events = frappe.db.count("Event")
	upcoming_events = frappe.db.count("Event",
		{"event_date": [">=", today()], "event_status": ["!=", "Cancelled"]},
	)
	total_guests = frappe.db.count("Guest")
	total_contributions = frappe.db.count("Contribution")

	contributions = frappe.get_all("Contribution", fields=["paid_amount"])
	total_amount = sum(c.paid_amount or 0 for c in contributions)

	return {
		"total_events": total_events,
		"upcoming_events": upcoming_events,
		"total_guests": total_guests,
		"total_contributions": total_contributions,
		"total_contribution_amount": total_amount,
	}


@frappe.whitelist()
def get_options():
	"""Get all reference options for dropdowns."""

	def get_names(doctype, field="name", filters=None, order_by="position ASC"):
		return [d[field] for d in frappe.get_all(doctype, filters=filters, fields=[field], order_by=order_by)]

	return {
		"event_types": get_names("Event Type", "event_type_name", order_by="event_type_name ASC"),
		"event_statuses": get_names("Event Status", "status_name"),
		"guest_categories": get_names("Guest Category", "category_name"),
		"contribution_types": get_names("Contribution Type", "type_name"),
		"rsvp_statuses": get_names("RSVP Status", "status", order_by="position ASC"),
	}
