# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json
import frappe


@frappe.whitelist()
def get_logs(event=None, action_category=None, action_type=None,
             guest=None, limit=50, offset=0):
	"""Get activity logs with optional filters."""
	filters = {}
	if event:
		filters["event"] = event
	if action_category:
		filters["action_category"] = action_category
	if action_type:
		filters["action_type"] = action_type
	if guest:
		filters["guest"] = guest

	logs = frappe.get_list(
		"Invite Activity Log",
		filters=filters,
		fields=[
			"name", "event", "guest", "guest_name",
			"action_type", "action_category", "subject", "details",
			"reference_doctype", "reference_name",
			"performed_by", "ip_address", "creation",
		],
		limit_page_length=limit,
		limit_start=offset,
		order_by="creation DESC",
	)

	total = frappe.db.count("Invite Activity Log", filters)

	# Enrich with user names
	for log in logs:
		if log.get("performed_by"):
			log["performed_by_name"] = frappe.db.get_value(
				"User", log["performed_by"], "full_name"
			) or log["performed_by"]

	return {"logs": logs, "total": total}


@frappe.whitelist()
def get_stats(event=None):
	"""Get summary stats for the activity log."""
	base_filters = {}
	if event:
		base_filters["event"] = event

	total = frappe.db.count("Invite Activity Log", base_filters)

	# Count by category
	categories = frappe.get_all(
		"Invite Activity Log",
		filters=base_filters,
		fields=["action_category", "count(name) as count"],
		group_by="action_category",
	)

	# Count by action type
	action_types = frappe.get_all(
		"Invite Activity Log",
		filters=base_filters,
		fields=["action_type", "count(name) as count"],
		group_by="action_type",
		order_by="count(name) DESC",
		limit=10,
	)

	return {
		"total": total,
		"categories": categories or [],
		"action_types": action_types or [],
	}


@frappe.whitelist()
def get_categories():
	"""Get distinct action categories."""
	return [
		"Guest Management", "Invitation", "Check-In",
		"RSVP", "Communication", "Card", "Frontdesk", "System",
	]
