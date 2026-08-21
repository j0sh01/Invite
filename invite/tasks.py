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
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Reminder: {event.event_name} is coming up!",
				"email": guest.email,
				"for_user": guest.email,
				"document_type": "Event",
				"document_name": event_name,
			}).insert(ignore_permissions=True)

		frappe.publish_realtime(
			"refetch_resource",
			{"cache_key": "invite.api.notification.get_notifications"},
			user=event.owner,
		)

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
		checked_in_guests = frappe.get_all(
			"Check-In",
			filters={"event": event_name, "is_duplicate": 0},
			fields=["guest", "guest_name"],
		)

		for checkin in checked_in_guests:
			guest = frappe.get_cached_doc("Guest", checkin.guest)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": f"Thank you for joining {event.event_name}!",
				"email": guest.email,
				"for_user": guest.email,
				"document_type": "Event",
				"document_name": event_name,
			}).insert(ignore_permissions=True)

		frappe.publish_realtime(
			"refetch_resource",
			{"cache_key": "invite.api.notification.get_notifications"},
			user=event.owner,
		)

	frappe.log_error(
		f"Sent thank you messages for {len(events)} events",
		"Invite Thank You Messages"
	)


def process_pending_invitations():
	"""Process pending invitations that haven't been sent yet.

	Only processes invitations that are in 'Ready' status and have a delivery method.
	Actually sends messages through the configured provider.
	"""
	pending = frappe.get_all(
		"Invitation",
		filters={"status": "Ready", "delivery_method": ["in", ["WhatsApp", "SMS"]]},
		pluck="name",
		limit=20,
	)

	if not pending:
		return

	sent_count = 0
	failed_count = 0

	for inv_name in pending:
		try:
			# Use the invitation's send_single_invitation function
			result = frappe.get_attr(
				"invite.invite.doctype.invitation.invitation.send_single_invitation"
			)(inv_name, frappe.db.get_value("Invitation", inv_name, "delivery_method") or "WhatsApp")
			if result.get("success"):
				sent_count += 1
			else:
				failed_count += 1
		except Exception as e:
			failed_count += 1
			frappe.log_error(
				f"Failed to process invitation {inv_name}: {e}",
				"Invite Pending Invitations"
			)

	frappe.log_error(
			f"Processed {len(pending)} pending invitations: {sent_count} sent, {failed_count} failed",
			"Invite Pending Invitations"
		)
