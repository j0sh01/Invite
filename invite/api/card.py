# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import get_url


@frappe.whitelist()
def generate_invitation_card(invitation):
	"""Generate a two-page invitation card PDF.

	Page 1 — Frappe's built-in Event print format (shows all event details
	         in the standard Frappe layout).
	Page 2 — Big centered QR code for scanning at the venue.

	If the event has no image uploaded, the request is rejected so that
	users upload an event image first before generating cards.
	"""
	from frappe.utils.pdf import get_pdf

	inv = frappe.get_doc("Invitation", invitation)
	event = frappe.get_doc("Event", inv.event)

	# Validate: event must have an image to generate a card
	if not event.image:
		frappe.throw(
			_("Please upload an Event Image in Event Settings before generating invitation cards."),
			title=_("Event Image Required")
		)

	# Auto-generate QR code if not present
	if not inv.qr_code_image:
		frappe.get_attr(
			"invite.doctype.invitation.invitation.generate_qr_code"
		)(invitation)
		inv.reload()

	# Step 1: Get Frappe's built-in Event print format HTML for page 1
	print_html = frappe.get_print(
		doctype="Event",
		name=event.name,
		print_format="Event",
		no_letterhead=1,
	)

	# Step 2: Generate the QR code page HTML
	qr_page_html = _build_qr_page_html(event, inv)

	# Step 3: Combine — insert QR styles into <head> and QR page before </body>
	qr_styles = _qr_page_styles()
	combined_html = print_html.replace("</head>", qr_styles + "\n\t</head>")
	combined_html = combined_html.replace("</body>", qr_page_html + "\n</body>")

	# Step 4: Convert combined HTML to PDF
	pdf_content = get_pdf(combined_html)

	import os
	from frappe.utils import get_site_path

	filename = f"invitation_{inv.invite_code}.pdf"
	path = os.path.join(get_site_path("public", "files"), filename)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "wb") as f:
		f.write(pdf_content)

	file_doc = frappe.get_doc({
		"doctype": "File",
		"file_url": f"/files/{filename}",
		"attached_to_doctype": "Invitation",
		"attached_to_name": invitation,
		"is_private": 0,
	})
	file_doc.insert(ignore_permissions=True)

	# Store the card URL on the invitation
	inv.db_set("personalized_invite_card", f"/files/{filename}")

	return {
		"card_url": f"/files/{filename}",
		"invite_code": inv.invite_code,
	}


@frappe.whitelist()
def download_invitation_card(invitation):
	"""Generate and return the card URL for download."""
	result = generate_invitation_card(invitation)
	frappe.response["type"] = "redirect"
	frappe.response["location"] = result["card_url"]
	return result


def _qr_page_styles():
	"""Return CSS styles for the QR code page (appended to Frappe's print format)."""
	return """
	<style>
		/* -- QR code page (page 2) -- */
		.qr-page {
			page-break-before: always;
			width: 210mm;
			height: 297mm;
		}
		.qr-page table {
			width: 100%;
			height: 100%;
		}
		.qr-page td {
			text-align: center;
			vertical-align: middle;
		}
		.qr-inner {
			display: inline-block;
			background: #f8f8f8;
			padding: 24px;
			border: 1px solid #eee;
		}
		.qr-inner img {
			width: 240px;
			height: 240px;
		}
		.qr-label {
			margin-top: 20px;
			font-size: 14px;
			color: #888;
			letter-spacing: 2px;
			text-transform: uppercase;
		}
		.invite-code {
			margin-top: 12px;
			font-size: 11px;
			color: #aaa;
			letter-spacing: 1px;
		}
	</style>
	"""


def _build_qr_page_html(event, inv):
	"""Build only the QR code page HTML (page 2).

	This gets appended to Frappe's built-in Event print format (page 1).
	"""
	qr_image_url = get_url(inv.qr_code_image) if inv.qr_code_image else ""
	qr_img = f'<img src="{qr_image_url}" alt="QR Code" />' if qr_image_url else '<p style="color:#ccc;font-size:16px;">No QR code available</p>'

	return f"""
	<div class="qr-page">
		<table>
			<tr>
				<td>
					<div class="qr-inner">
						{qr_img}
					</div>
					<div class="qr-label">Scan to check in</div>
					<div class="invite-code">{inv.invite_code}</div>
				</td>
			</tr>
		</table>
	</div>
	"""


# ──────────────────────────────────────────────
#  Multi-channel Reminders
# ──────────────────────────────────────────────


@frappe.whitelist()
def send_reminders(event, channel=None, reminder_type="event"):
	"""Send reminders for an event via specified channel.
	
	channel: "WhatsApp" | "SMS" | "Email" | None (all)
	reminder_type: "event" | "contribution" | "thank_you"
	"""
	event_doc = frappe.get_doc("Event", event)

	if reminder_type == "thank_you":
		return _send_thank_you_messages(event_doc, channel)
	elif reminder_type == "contribution":
		return _send_contribution_reminders(event_doc, channel)
	else:
		return _send_event_reminders(event_doc, channel)


def _send_event_reminders(event_doc, channel):
	"""Send event reminders with invitation card attachment and RSVP link."""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event_doc.name},
		fields=["name", "full_name", "email", "mobile_no", "guest_type", "invite_code"],
	)

	base_url = get_url()
	# Use getattr for fields that may not exist before migration
	message = getattr(event_doc, "invitation_message", None) or (
		"Dear {guest_name}, you are invited to {event_name} on {event_date} at {venue}.\n\n"
		"Please RSVP here: {rsvp_link}"
	)
	sent = []
	failed = []

	for guest in guests:
		try:
			rsvp_link = f"{base_url}/rsvp?code={guest.invite_code}"
			personalized = message \
				.replace("{guest_name}", guest.full_name or "Guest") \
				.replace("{event_name}", event_doc.event_name) \
				.replace("{event_date}", str(event_doc.event_date or "")) \
				.replace("{venue}", event_doc.venue or "") \
				.replace("{rsvp_link}", rsvp_link)

			# Find invitation card attachment
			invitation = frappe.db.get_value("Invitation", {
				"event": event_doc.name, "guest": guest.name
			}, ["name", "personalized_invite_card"], as_dict=True)

			card_path = invitation.personalized_invite_card if invitation else None

			if channel in (None, "Email") and guest.email:
				_send_email(guest.email, f"Reminder: {event_doc.event_name}", personalized, card_path)
				sent.append({"guest": guest.name, "channel": "Email"})

			if channel in (None, "WhatsApp"):
				_send_whatsapp(guest.mobile_no, personalized, card_path, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, personalized, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Reminder: {event_doc.event_name}")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})
			frappe.log_error(
				f"Event reminder failed for {guest.name}: {frappe.get_traceback()}",
				"Send Reminder"
			)

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total_sent": len(sent), "total_failed": len(failed)}


def _send_contribution_reminders(event_doc, channel):
	"""Send contribution reminders to guests with outstanding amounts.
	Only sends to guests where outstanding_amount > 0.
	"""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event_doc.name, "outstanding_amount": [">", 0]},
		fields=["name", "full_name", "email", "mobile_no", "outstanding_amount"],
	)

	if not guests:
		return {"sent": [], "failed": [], "total_sent": 0, "total_failed": 0, "message": "No guests with outstanding contributions."}

	currency = event_doc.currency or "TZS"
	sent = []
	failed = []

	for guest in guests:
		try:
			amount_str = f"{currency} {guest.outstanding_amount:,.0f}"
			msg = (
				f"Dear {guest.full_name}, this is a friendly reminder that you have an "
				f"outstanding contribution of {amount_str} for {event_doc.event_name}. "
				f"Thank you for your generous support!"
			)

			if channel in (None, "Email") and guest.email:
				_send_email(guest.email, f"Contribution Reminder: {event_doc.event_name}", msg)
				sent.append({"guest": guest.name, "channel": "Email"})

			if channel in (None, "WhatsApp"):
				_send_whatsapp(guest.mobile_no, msg, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, msg, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Contribution Reminder: {event_doc.event_name}")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})
			frappe.log_error(
				f"Contribution reminder failed for {guest.name}: {frappe.get_traceback()}",
				"Send Reminder"
			)

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total_sent": len(sent), "total_failed": len(failed)}


def _send_thank_you_messages(event_doc, channel):
	"""Send thank you messages after event with event image."""
	checked_in_guests = frappe.get_all(
		"Check-In",
		filters={"event": event_doc.name, "is_duplicate": 0},
		fields=["guest", "guest_name"],
	)

	template = event_doc.thank_you_template or "Dear {guest_name}, thank you for attending {event_name}! We truly appreciate your presence."
	sent = []
	failed = []

	for ci in checked_in_guests:
		try:
			guest = frappe.get_cached_doc("Guest", ci.guest)
			personalized = template \
				.replace("{guest_name}", guest.full_name or "Guest") \
				.replace("{event_name}", event_doc.event_name)

			if channel in (None, "Email") and guest.email:
				_send_email(guest.email, f"Thank You: {event_doc.event_name}", personalized, event_doc.image)
				sent.append({"guest": guest.name, "channel": "Email"})

			if channel in (None, "WhatsApp"):
				_send_whatsapp(guest.mobile_no, personalized, event_doc.image, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, personalized, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Thank you for joining {event_doc.event_name}!")

		except Exception as e:
			failed.append({"guest": ci.guest, "error": str(e)})
			frappe.log_error(
				f"Thank you message failed for {ci.guest}: {frappe.get_traceback()}",
				"Send Reminder"
			)

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total_sent": len(sent), "total_failed": len(failed)}


# ──────────────────────────────────────────────
#  Channel Dispatch Helpers
# ──────────────────────────────────────────────


def _send_email(recipient, subject, message, attachment_path=None):
	"""Queue an email with optional attachment (file URL)."""
	import json
	from frappe.email.doctype.email_queue.email_queue import EmailQueue

	if not recipient:
		return

	email_queue = EmailQueue.new({
		"sender": frappe.session.user,
		"recipients": [recipient],
		"subject": subject,
		"message": message,
		"reference_doctype": "Event",
	}, ignore_permissions=True)

	if email_queue and attachment_path:
		try:
			# Store as file_url so Frappe's SendMailContext.include_attachments()
			# can resolve the file content at send time
			attachments = json.loads(email_queue.attachments) if email_queue.attachments else []
			attachments.append({"file_url": attachment_path})
			email_queue.db_set("attachments", json.dumps(attachments))
		except Exception as e:
			frappe.log_error(f"Failed to attach file to email: {e}", "Send Email")


def _send_whatsapp(mobile_no, message, attachment_path=None, event_name=None):
	"""Send WhatsApp message with optional card/image attachment.
	
	Uses WhatsApp Cloud API if configured, otherwise logs to Notification Log.
	
	If attachment_path is provided, it is sent as a media attachment
	(image or document) along with the message text as caption.
	"""
	mobile = str(mobile_no or "").strip()
	message = message or ""
	attachment_path = attachment_path or ""

	# Try to send via WhatsApp Cloud API
	from invite.api.whatsapp import (
		get_whatsapp_config,
		send_media_message,
		send_text_message,
	)

	config = get_whatsapp_config()
	api_sent = False

	if config["enabled"] and mobile:
		if attachment_path:
			# Pass the file path directly for Frappe's get_file() to resolve
			# attachment_path is already in /files/filename.pdf format
			if attachment_path.startswith("http"):
				file_path = attachment_path
			elif attachment_path.startswith("/"):
				file_path = attachment_path
			else:
				file_path = f"/{attachment_path}"

			# Only attempt media if path is non-empty
			if file_path.strip("/"):
				success, _ = send_media_message(mobile, message, file_path)
				api_sent = success
			else:
				success = send_text_message(mobile, message)
				api_sent = success
		else:
			success = send_text_message(mobile, message)
			api_sent = success

	# Always log the notification for audit trail
	attach_info = f" [Attachment API Sent]" if attachment_path and api_sent else (
		f" [Attachment: {attachment_path}]" if attachment_path else ""
	)
	log_subject = f"WhatsApp: {(message or '')[:80]}...{attach_info}"

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": log_subject,
		"email": mobile or "unknown",
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_name or "",
	}).insert(ignore_permissions=True)


def _send_sms(mobile_no, message, event_name=None):
	"""Log SMS message.
	Actual sending would integrate with an SMS provider like Beem/Africastalking.
	"""
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": f"SMS: {message[:80]}...",
		"email": str(mobile_no or "").strip() or "unknown",
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_name or "",
	}).insert(ignore_permissions=True)


def _log_notification(guest, event_doc, subject):
	"""Log a notification for audit trail and push real-time update."""
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email": str(guest.email or guest.mobile_no or "").strip() or "unknown",
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_doc.name,
	}).insert(ignore_permissions=True)

	# Push real-time update so the sidebar refreshes immediately
	frappe.publish_realtime(
		"refetch_resource",
		{"cache_key": "invite.api.notification.get_notifications"},
		user=frappe.session.user,
	)
