# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import today, add_days, getdate, now


def send_reminder_notifications():
	"""Send daily reminders for events happening soon."""
	reminder_date = add_days(today(), 3)

	events = frappe.get_all(
		"Event",
		filters={
			"event_date": reminder_date,
			"enable_reminders": 1,
			"event_status": ["!=", "Cancelled"],
		},
		pluck="name",
	)

	for event_name in events:
		event = frappe.get_doc("Event", event_name)
		# Find guests who haven't RSVPed yet
		pending_guests = frappe.get_all(
			"Guest",
			filters={
				"event": event_name,
				"rsvp_status": ["in", ["", "Pending"]],
			},
			pluck="name",
		)

		for guest_name in pending_guests:
			guest = frappe.get_cached_doc("Guest", guest_name)
			# Log reminder (actual sending would integrate with Beem/SMS/WhatsApp)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Reminder: {event.event_name} is coming up!",
				"email": guest.email,
				"for_user": guest.email,
				"document_type": "Event",
				"document_name": event_name,
			}).insert(ignore_permissions=True)

	frappe.log_error(
		f"Sent reminders for {len(events)} events",
		"Invite Reminder Notifications"
	)


def send_thank_you_messages():
	"""Send thank you messages after events."""
	events = frappe.get_all(
		"Event",
		filters={
			"event_date": ["<", today()],
			"event_status": "Completed",
		},
		pluck="name",
	)

	for event_name in events:
		event = frappe.get_doc("Event", event_name)
		# Find guests who attended
		checked_in_guests = frappe.get_all(
			"Check-In",
			filters={"event": event_name, "is_duplicate": 0},
			fields=["guest", "guest_name"],
		)

		for checkin in checked_in_guests:
			guest = frappe.get_cached_doc("Guest", checkin.guest)
			# Create notification log (actual sending would integrate with Beem/SMS/WhatsApp)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Thank you for joining {event.event_name}!",
				"email": guest.email,
				"for_user": guest.email,
				"document_type": "Event",
				"document_name": event_name,
			}).insert(ignore_permissions=True)

	frappe.log_error(
		f"Sent thank you messages for {len(events)} events",
		"Invite Thank You Messages"
	)


def send_contribution_reminders():
	"""Send automated contribution reminders for events with outstanding amounts."""
	events = frappe.get_all(
		"Event",
		filters={"event_status": ["in", ["RSVPs Open", "Ongoing", "Invitations Sent"]]},
		pluck="name",
	)

	for event_name in events:
		guests_with_outstanding = frappe.get_all(
			"Guest",
			filters={
				"event": event_name,
				"outstanding_amount": [">", 0],
			},
			fields=["name", "full_name", "email", "mobile_no", "outstanding_amount"],
		)

		if not guests_with_outstanding:
			continue

		event = frappe.get_cached_doc("Event", event_name)
		currency = event.currency or "TZS"

		for guest in guests_with_outstanding:
			message = (
				f"Dear {guest.full_name}, this is a friendly reminder that you have an "
				f"outstanding contribution of {currency} {guest.outstanding_amount:,.0f} "
				f"for {event.event_name}. Thank you for your generous support!"
			)

			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Contribution Reminder: {event.event_name}",
				"email": guest.email or guest.mobile_no,
				"for_user": guest.email or guest.mobile_no,
				"document_type": "Event",
				"document_name": event_name,
			}).insert(ignore_permissions=True)

		frappe.log_error(
			f"Sent contribution reminders for {len(guests_with_outstanding)} guests in {event_name}",
			"Invite Contribution Reminders"
		)

	if not events:
		frappe.log_error("No events found for contribution reminders", "Invite Contribution Reminders")


def process_pending_invitations():
	"""Process pending invitations (mark as sent, etc.)."""
	# This would be where actual integration with messaging providers happens
	pending = frappe.get_all(
		"Invitation",
		filters={"status": "Ready", "delivery_status": "Pending"},
		pluck="name",
		limit=50,
	)

	for inv_name in pending:
		inv = frappe.get_doc("Invitation", inv_name)
		# Simulate sending (in production, call Beem/WhatsApp API)
		inv.status = "Sent"
		inv.sent_at = now()
		inv.delivery_status = "Delivered"
		inv.delivered_at = now()
		inv.save(ignore_permissions=True)

	if pending:
		frappe.log_error(
			f"Processed {len(pending)} pending invitations",
			"Invite Pending Invitations"
		)
