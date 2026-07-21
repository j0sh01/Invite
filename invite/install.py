# Copyright (c) 2024, Joshua Michael and Contributors
# MIT License. See license.txt
import frappe


def before_install():
	pass


def after_install(force=False):
	add_default_event_types()
	add_default_event_statuses()
	add_default_guest_categories()
	add_default_contribution_types()
	add_default_rsvp_statuses()
	create_event_settings()
	frappe.db.commit()


def add_default_event_types():
	"""Create default event type categories."""
	types = [
		"Wedding",
		"Funeral",
		"Harambee",
		"Graduation",
		"Church Event",
		"Birthday",
		"Corporate Event",
		"Other",
	]

	for event_type in types:
		if frappe.db.exists("Event Type", event_type):
			continue
		doc = frappe.new_doc("Event Type")
		doc.event_type_name = event_type
		doc.insert()


def add_default_event_statuses():
	"""Create default event lifecycle statuses."""
	statuses = [
		{"status_name": "Planning", "color": "blue", "position": 1},
		{"status_name": "Invitations Sent", "color": "orange", "position": 2},
		{"status_name": "RSVPs Open", "color": "purple", "position": 3},
		{"status_name": "Ongoing", "color": "yellow", "position": 4},
		{"status_name": "Completed", "color": "green", "position": 5},
		{"status_name": "Cancelled", "color": "red", "position": 6},
	]

	for status in statuses:
		if frappe.db.exists("Event Status", status["status_name"]):
			continue
		doc = frappe.new_doc("Event Status")
		doc.status_name = status["status_name"]
		doc.color = status["color"]
		doc.position = status["position"]
		doc.insert()


def add_default_guest_categories():
	"""Create default guest categorization."""
	categories = [
		{"category_name": "Family", "position": 1},
		{"category_name": "Friend", "position": 2},
		{"category_name": "Colleague", "position": 3},
		{"category_name": "Neighbor", "position": 4},
		{"category_name": "VIP", "position": 5},
		{"category_name": "Committee", "position": 6},
		{"category_name": "Other", "position": 7},
	]

	for cat in categories:
		if frappe.db.exists("Guest Category", cat["category_name"]):
			continue
		doc = frappe.new_doc("Guest Category")
		doc.category_name = cat["category_name"]
		doc.position = cat["position"]
		doc.insert()


def add_default_contribution_types():
	"""Create default contribution/payment types."""
	types = [
		{"type_name": "Cash Contribution", "is_cash": 1, "position": 1},
		{"type_name": "In-Kind Contribution", "is_cash": 0, "position": 2},
		{"type_name": "Mobile Money", "is_cash": 1, "position": 3},
		{"type_name": "Bank Transfer", "is_cash": 1, "position": 4},
	]

	for t in types:
		if frappe.db.exists("Contribution Type", t["type_name"]):
			continue
		doc = frappe.new_doc("Contribution Type")
		doc.type_name = t["type_name"]
		doc.is_cash = t["is_cash"]
		doc.position = t["position"]
		doc.insert()


def add_default_rsvp_statuses():
	"""Create default RSVP statuses."""
	statuses = [
		{"status": "Pending", "color": "gray"},
		{"status": "Accepted", "color": "green"},
		{"status": "Declined", "color": "red"},
		{"status": "Maybe", "color": "orange"},
	]

	for s in statuses:
		if frappe.db.exists("RSVP Status", s["status"]):
			continue
		doc = frappe.new_doc("RSVP Status")
		doc.status = s["status"]
		doc.color = s["color"]
		doc.insert()


def create_event_settings():
	"""Create default Event Settings singleton if not exists."""
	if frappe.db.exists("Event Settings", "Event Settings"):
		return

	settings = frappe.new_doc("Event Settings")
	settings.default_currency = "TZS"
	settings.insert()
