# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe


@frappe.whitelist()
def get_list(event, filters=None, limit=50, offset=0):
	"""Get check-ins for an event."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = {"event": event}
	if filters:
		base_filters.update(filters)

	checkins = frappe.get_list("Check-In",
		filters=base_filters,
		fields=["name", "guest", "guest_name", "invite_code", "invitation",
			"checked_in_at", "checked_in_by", "check_in_method",
			"number_of_attendees", "is_duplicate", "notes"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="checked_in_at DESC",
	)

	total = frappe.db.count("Check-In", base_filters)

	return {"checkins": checkins, "total": total}


@frappe.whitelist()
def get_stats(event):
	"""Get check-in statistics."""
	return frappe.get_attr("invite.invite.doctype.check_in.check_in.get_checkin_stats")(event)


@frappe.whitelist()
def search_guests(event, query):
	"""Search guests for manual check-in."""
	return frappe.get_all("Guest",
		filters={"event": event, "checked_in": 0},
		or_filters={
			"full_name": ["like", f"%{query}%"],
			"invite_code": ["like", f"%{query}%"],
			"mobile_no": ["like", f"%{query}%"],
			"email": ["like", f"%{query}%"],
		},
		fields=["name", "full_name", "invite_code", "mobile_no", "rsvp_status", "category"],
		limit=20,
	)
