# Copyright (c) 2024, Joshua Michael and Contributors
# MIT License. See license.txt
import frappe


def before_install():
	pass


def after_install(force=False):
	add_default_event_types()
	add_default_event_statuses()
	add_default_guest_categories()
	add_default_rsvp_statuses()
	create_event_settings()
	add_default_message_templates()
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


def add_default_message_templates():
	"""Create default message templates."""
	templates = [
		{
			"template_name": "Event Invitation",
			"template_type": "Event Invitation",
			"channel": "WhatsApp",
			"body": "Dear {guest_name},\n\nYou are invited to {event_name}!\n\n📅 Date: {event_date}\n🕐 Time: {event_time}\n📍 Venue: {venue}\n\nPlease RSVP here: {rsvp_link}\n\nWe look forward to seeing you!",
		},
		{
			"template_name": "RSVP Confirmation",
			"template_type": "RSVP Confirmation",
			"channel": "WhatsApp",
			"body": "Thank you, {guest_name}! Your attendance for {event_name} has been confirmed.\n\n📅 Date: {event_date}\n📍 Venue: {venue}\n\nSee you there!",
		},
		{
			"template_name": "Event Reminder",
			"template_type": "Event Reminder",
			"channel": "WhatsApp",
			"body": "Hi {guest_name},\n\nThis is a friendly reminder that {event_name} is coming up!\n\n📅 Date: {event_date}\n📍 Venue: {venue}\n\nPlease RSVP if you haven't already: {rsvp_link}",
		},
		{
			"template_name": "Thank You",
			"template_type": "Thank You",
			"channel": "WhatsApp",
			"body": "Dear {guest_name},\n\nThank you for attending {event_name}! We truly appreciate your presence and support.\n\nBest regards,\nThe Organizing Committee",
		},
	]

	for template in templates:
		if frappe.db.exists("Message Template", template["template_name"]):
			continue
		doc = frappe.new_doc("Message Template")
		doc.update(template)
		doc.enabled = 1
		doc.insert()
