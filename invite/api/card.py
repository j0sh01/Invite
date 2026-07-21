# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import get_url, today


@frappe.whitelist()
def generate_invitation_card(invitation):
	"""Generate an invitation card PDF with QR code and event details."""
	from frappe.utils.pdf import get_pdf

	inv = frappe.get_doc("Invitation", invitation)
	event = frappe.get_doc("Event", inv.event)

	# Auto-generate QR code if not present
	if not inv.qr_code_image:
		frappe.get_attr(
			"invite.invite.doctype.invitation.invitation.generate_qr_code"
		)(invitation)
		inv.reload()

	# Get QR position from event settings (default: Right)
	qr_position = getattr(event, "qr_position", None) or "Right"

	card_html = _build_card_html(event, inv, qr_position)
	pdf_content = get_pdf(card_html)

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


def _format_time(time_val):
	"""Format a time value (timedelta or time) to HH:MM AM/PM string."""
	if hasattr(time_val, "strftime"):
		return time_val.strftime("%I:%M %p")
	# timedelta object: extract hours and minutes
	total_seconds = int(time_val.total_seconds())
	hours = total_seconds // 3600
	minutes = (total_seconds % 3600) // 60
	period = "AM" if hours < 12 else "PM"
	if hours == 0:
		hours_12 = 12
	elif hours > 12:
		hours_12 = hours - 12
	else:
		hours_12 = hours
	return f"{hours_12}:{minutes:02d} {period}"


def _build_card_html(event, inv, qr_position="Right"):
	"""Build a single-page invitation card with the event photo as full background
	and QR code overlaid at the bottom (Left / Center / Right).

	qr_position: 'Left', 'Center', or 'Right' — controls QR code placement at bottom.
	"""
	event_image = get_url(event.image) if event.image else ""
	qr_image_url = get_url(inv.qr_code_image) if inv.qr_code_image else ""
	event_date = event.event_date.strftime("%d %B %Y") if event.event_date else ""
	event_time = _format_time(event.event_time) if event.event_time else ""

	# QR code horizontal alignment at the bottom of the card
	qr_align = qr_position.lower()  # left, center, right
	if qr_align == "left":
		qr_container_style = "left: 36px; transform: none;"
	elif qr_align == "center":
		qr_container_style = "left: 50%; transform: translateX(-50%);"
	else:  # right (default)
		qr_container_style = "right: 36px; transform: none;"

	# Background style: full-bleed image or fallback gradient
	if event_image:
		bg_style = f"background: url('{event_image}') center center / cover no-repeat;"
	else:
		bg_style = "background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);"

	return f"""
	<!DOCTYPE html>
	<html>
	<head>
		<meta charset="utf-8">
		<style>
			@page {{
				size: A4 portrait;
				margin: 0;
			}}
			* {{
				box-sizing: border-box;
			}}
			body {{
				margin: 0;
				padding: 0;
				width: 210mm;
				height: 297mm;
				overflow: hidden;
				font-family: 'Helvetica', 'Arial', sans-serif;
			}}

			/* ── Full-bleed card ── */
			.card {{
				position: relative;
				width: 100%;
				height: 100%;
				{bg_style}
			}}

			/* ── Dark overlay for text readability ── */
			.overlay {{
				position: absolute;
				inset: 0;
				background: rgba(0, 0, 0, 0.45);
				display: flex;
				flex-direction: column;
				justify-content: center;
				align-items: center;
				padding: 48px 40px 140px;
				text-align: center;
				color: #fff;
			}}

			/* ── Event name ── */
			.event-name {{
				font-size: 36px;
				font-weight: 700;
				letter-spacing: 1px;
				margin-bottom: 20px;
				text-shadow: 0 2px 8px rgba(0,0,0,0.5);
				line-height: 1.2;
			}}

			/* ── Decorative divider ── */
			.divider {{
				width: 80px;
				height: 3px;
				background: rgba(255,255,255,0.7);
				margin: 0 auto 20px;
				border-radius: 2px;
			}}

			/* ── Details block ── */
			.details {{
				font-size: 15px;
				line-height: 1.8;
				opacity: 0.92;
				text-shadow: 0 1px 4px rgba(0,0,0,0.4);
			}}
			.details .row {{
				margin-bottom: 4px;
			}}
			.details .label {{
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.5px;
				font-size: 11px;
				opacity: 0.75;
				display: block;
			}}

			/* ── Organiser badge ── */
			.organizer {{
				margin-top: 24px;
				padding: 10px 24px;
				background: rgba(0, 0, 0, 0.35);
				border-radius: 8px;
				font-size: 13px;
				line-height: 1.6;
			}}
			.organizer .label {{
				font-weight: 600;
				text-transform: uppercase;
				letter-spacing: 0.5px;
				font-size: 10px;
				opacity: 0.75;
				display: block;
			}}

			/* ── QR code container (bottom area) ── */
			.qr-container {{
				position: absolute;
				bottom: 36px;
				{qr_container_style}
				text-align: center;
				background: #fff;
				padding: 8px;
				border-radius: 8px;
				box-shadow: 0 4px 20px rgba(0,0,0,0.4);
			}}
			.qr-container img {{
				width: 110px;
				height: 110px;
				display: block;
				margin: 0 auto;
				border-radius: 4px;
			}}
			.qr-label {{
				margin-top: 6px;
				font-size: 9px;
				color: #666;
				letter-spacing: 1px;
				text-transform: uppercase;
			}}

			/* ── Footer ── */
			.footer {{
				position: absolute;
				bottom: 10px;
				left: 0;
				right: 0;
				text-align: center;
				font-size: 8px;
				color: rgba(255,255,255,0.4);
				letter-spacing: 0.5px;
			}}
		</style>
	</head>
	<body>
		<div class="card">
			<div class="overlay">
				<div class="event-name">{event.event_name}</div>
				<div class="divider"></div>
				<div class="details">
					<div class="row">
						<span class="label">Date</span>
						{event_date}
					</div>
					{f'<div class="row"><span class="label">Time</span>{event_time}</div>' if event_time else ''}
					{f'<div class="row"><span class="label">Venue</span>{event.venue}</div>' if event.venue else ''}
					{f'<div class="row"><span class="label">Address</span>{event.location_address}</div>' if event.location_address else ''}
				</div>
				<div class="organizer">
					<span class="label">Organized by</span>
					{event.organizer_name}
					{f'<br>{event.organizer_contact}' if event.organizer_contact else ''}
				</div>
			</div>

			<div class="qr-container">
				{f'<img src="{qr_image_url}" alt="QR Code" />' if qr_image_url else ''}
				<div class="qr-label">Scan to check in</div>
			</div>

			<div class="footer">
				Generated by Invite | {inv.invite_code}
			</div>
		</div>
	</body>
	</html>
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
				_send_whatsapp(guest.mobile_no, personalized, card_path)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, personalized)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Reminder: {event_doc.event_name}")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})

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
				_send_whatsapp(guest.mobile_no, msg)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, msg)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Contribution Reminder: {event_doc.event_name}")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})

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
				_send_whatsapp(guest.mobile_no, personalized, event_doc.image)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			if channel in (None, "SMS") and guest.mobile_no:
				_send_sms(guest.mobile_no, personalized)
				sent.append({"guest": guest.name, "channel": "SMS"})

			_log_notification(guest, event_doc, f"Thank you for joining {event_doc.event_name}!")

		except Exception as e:
			failed.append({"guest": ci.guest, "error": str(e)})

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total_sent": len(sent), "total_failed": len(failed)}


# ──────────────────────────────────────────────
#  Channel Dispatch Helpers
# ──────────────────────────────────────────────


def _send_email(recipient, subject, message, attachment_path=None):
	"""Queue an email with optional attachment."""
	import os
	from frappe.email.doctype.email_queue.email_queue import EmailQueue

	email_queue = EmailQueue.new({
		"sender": frappe.session.user,
		"recipients": [recipient],
		"subject": subject,
		"message": message,
		"reference_doctype": "Event",
	}, ignore_permissions=True)

	if email_queue and attachment_path:
		try:
			# Resolve file URL to actual file content
			from frappe.utils.file_manager import get_file
			file_content, filename, _ = get_file(attachment_path)
			email_queue.append("attachments", {
				"fcontent": file_content,
				"fname": filename or os.path.basename(attachment_path),
			})
			email_queue.save(ignore_permissions=True)
		except Exception:
			# Silently skip attachment if file not found
			pass


def _send_whatsapp(mobile_no, message, attachment_path=None):
	"""Log WhatsApp message with optional attachment card/image.
	
	If attachment_path is provided, the file is stored alongside the log
	so the WhatsApp integration service can send it as a media message.
	Actual sending would integrate with a WhatsApp Business API.
	
	For media messages, the attachment should be a publicly accessible
	URL or file path to an image/PDF that will be sent as a WhatsApp
	media attachment.
	"""
	from frappe.utils import get_url

	# Build subject with attachment info
	attach_info = f" [Attachment: {attachment_path}]" if attachment_path else ""
	log_subject = f"WhatsApp: {message[:80]}...{attach_info}"

	note = frappe.get_doc({
		"doctype": "Notification Log",
		"subject": log_subject,
		"email": str(mobile_no or "").strip() or "unknown",
		"for_user": frappe.session.user,
	})
	note.insert(ignore_permissions=True)

	# If we had a WhatsApp Business API configured, we would send here:
	# _send_whatsapp_media_via_api(mobile_no, message, attachment_url)


def _send_sms(mobile_no, message):
	"""Log SMS message.
	Actual sending would integrate with an SMS provider like Beem/Africastalking.
	"""
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": f"SMS: {message[:80]}...",
		"email": str(mobile_no or "").strip() or "unknown",
		"for_user": frappe.session.user,
	}).insert(ignore_permissions=True)


def _log_notification(guest, event_doc, subject):
	"""Log a notification for audit trail."""
	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email": str(guest.email or guest.mobile_no or "").strip() or "unknown",
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_doc.name,
	}).insert(ignore_permissions=True)
