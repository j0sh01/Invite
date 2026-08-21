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
			"Please upload an Event Image in Event Settings before generating invitation cards.",
			title="Event Image Required"
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

	# Step 3: Build guest name banner HTML
	guest_banner_html = _build_guest_banner_html(inv)

	# Step 4: Combine — insert styles into <head>, banner at top of body, QR page before </body>
	qr_styles = _qr_page_styles()
	combined_html = print_html.replace("</head>", qr_styles + "\n\t</head>")
	combined_html = combined_html.replace("<body>", "<body>\n" + guest_banner_html)
	combined_html = combined_html.replace("</body>", qr_page_html + "\n</body>")

	# Step 5: Convert combined HTML to PDF
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

	# Audit log
	try:
		from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
		log_action(
			event=inv.event,
			action_type="Invitation Card Generated",
			subject=f"Personalized card generated for {inv.guest_name}",
			guest=inv.guest,
			guest_name=inv.guest_name,
			reference_doctype="Invitation",
			reference_name=inv.name,
			extra_data={"invite_code": inv.invite_code, "card_url": f"/files/{filename}"},
		)
	except Exception:
		pass

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
	"""Return CSS styles for guest name banner and QR code page."""
	return """
	<style>
		/* -- Guest name banner (inserted at top of page 1) -- */
		.guest-banner {
			padding: 28px 32px 22px;
			text-align: center;
			border-bottom: 3px solid #e2e8f0;
			background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
		}
		.guest-banner .guest-label {
			font-size: 11px;
			letter-spacing: 3px;
			text-transform: uppercase;
			color: #94a3b8;
			margin-bottom: 8px;
		}
		.guest-banner .guest-name {
			font-size: 28px;
			font-weight: 700;
			color: #1e293b;
			margin: 0;
			line-height: 1.3;
		}
		.guest-banner .guest-invite-code {
			font-size: 10px;
			color: #94a3b8;
			margin-top: 8px;
			letter-spacing: 2px;
			font-family: monospace;
		}
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


def _build_guest_banner_html(inv):
	"""Build the guest name banner HTML (inserted at top of page 1)."""
	guest_name = inv.guest_name or "Valued Guest"
	invite_code = inv.invite_code or ""
	return f"""
	<div class="guest-banner">
		<div class="guest-label">You are cordially invited</div>
		<div class="guest-name">{guest_name}</div>
		<div class="guest-invite-code">{invite_code}</div>
	</div>
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

	channel: "WhatsApp" | "Email" | None (all)
	reminder_type: "event" | "thank_you"
	"""
	event_doc = frappe.get_doc("Event", event)

	if reminder_type == "thank_you":
		return _send_thank_you_messages(event_doc, channel)
	else:
		return _send_event_reminders(event_doc, channel)


def _send_event_reminders(event_doc, channel):
	"""Send event reminders with invitation card attachment and RSVP link."""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event_doc.name},
		fields=["name", "full_name", "email", "mobile_no", "invite_code"],
	)

	base_url = get_url()
	message = (
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

			if channel in (None, "WhatsApp") and guest.mobile_no:
				_send_whatsapp(guest.mobile_no, personalized, card_path, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			_log_notification(guest, event_doc, f"Reminder: {event_doc.event_name}")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})
			frappe.log_error(
				f"Event reminder failed for {guest.name}: {frappe.get_traceback()}",
				"Send Reminder"
			)

	# Audit log for reminders
	if sent:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=event_doc.name,
				action_type="Reminder Sent",
				subject=f"{len(sent)} reminder(s) sent for {event_doc.event_name}",
				extra_data={"sent_count": len(sent), "failed_count": len(failed), "channel": channel},
			)
		except Exception:
			pass

	frappe.db.commit()
	return {"sent": sent, "failed": failed, "total_sent": len(sent), "total_failed": len(failed)}


def _send_thank_you_messages(event_doc, channel):
	"""Send thank you messages after event with event image."""
	checked_in_guests = frappe.get_all(
		"Check-In",
		filters={"event": event_doc.name, "is_duplicate": 0},
		fields=["guest", "guest_name"],
	)

	template = "Dear {guest_name}, thank you for attending {event_name}! We truly appreciate your presence."
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

			if channel in (None, "WhatsApp") and guest.mobile_no:
				_send_whatsapp(guest.mobile_no, personalized, event_doc.image, event_name=event_doc.name)
				sent.append({"guest": guest.name, "channel": "WhatsApp"})

			_log_notification(guest, event_doc, f"Thank you for joining {event_doc.event_name}!")

		except Exception as e:
			failed.append({"guest": ci.guest, "error": str(e)})
			frappe.log_error(
				f"Thank you message failed for {ci.guest}: {frappe.get_traceback()}",
				"Send Reminder"
			)

	# Audit log for thank you messages
	if sent:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=event_doc.name,
				action_type="Thank You Sent",
				subject=f"{len(sent)} thank you message(s) sent for {event_doc.event_name}",
				extra_data={"sent_count": len(sent), "failed_count": len(failed), "channel": channel},
			)
		except Exception:
			pass

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
			attachments = json.loads(email_queue.attachments) if email_queue.attachments else []
			attachments.append({"file_url": attachment_path})
			email_queue.db_set("attachments", json.dumps(attachments))
		except Exception as e:
			frappe.log_error(f"Failed to attach file to email: {e}", "Send Email")


def _send_whatsapp(mobile_no, message, attachment_path=None, event_name=None):
	"""Send WhatsApp message via configured provider (Official API or Twilio)."""
	mobile = str(mobile_no or "").strip()
	message = message or ""

	settings = frappe.get_single("Event Settings")
	provider = getattr(settings, "whatsapp_provider", "")

	api_sent = False

	if provider == "Official WhatsApp API" and mobile:
		from invite.api.whatsapp import get_whatsapp_config, send_media_message, send_text_message
		config = get_whatsapp_config()
		if config["enabled"]:
			if attachment_path:
				if attachment_path.startswith("http"):
					file_path = attachment_path
				elif attachment_path.startswith("/"):
					file_path = attachment_path
				else:
					file_path = f"/{attachment_path}"
				if file_path.strip("/"):
					success, _ = send_media_message(mobile, message, file_path)
					api_sent = success
			else:
				success = send_text_message(mobile, message)
				api_sent = success

	elif provider == "Twilio" and mobile:
		from invite.api.twilio import send_whatsapp_message, send_template_message, get_template_sids
		# Try Content API template first, fall back to plain text
		template_type = _get_template_type_for_reminder(message)
		tids = get_template_sids()
		template_sid = tids.get(template_type, "") if template_type else ""

		if template_sid and template_type:
			# Build template variables from message context
			variables = _build_template_variables(message, template_type)
			success = send_template_message(mobile, template_sid, variables)
		else:
			success = send_whatsapp_message(mobile, message, attachment_path)
		api_sent = success

	# Always log the notification for audit trail
	status = "API Sent" if api_sent else "Logged"
	log_subject = f"WhatsApp [{status}]: {(message or '')[:80]}..."

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": log_subject,
		"email": mobile or "unknown",
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_name or "",
	}).insert(ignore_permissions=True)


def _get_template_type_for_reminder(message):
	"""Determine the template type based on message content."""
	msg = (message or "").lower()
	if "thank you" in msg or "appreciate" in msg:
		return "thank_you"
	elif "reminder" in msg:
		return "event_reminder"
	elif "rsvp" in msg and "confirm" in msg:
		return "rsvp_confirmation"
	elif "rsvp" in msg and "remind" in msg:
		return "rsvp_reminder"
	elif "invited" in msg or "invitation" in msg:
		return "event_invitation"
	elif "update" in msg or "changed" in msg:
		return "event_update"
	elif "check-in" in msg or "qr" in msg:
		return "qr_checkin"
	return None


def _build_template_variables(message, template_type):
	"""Build Content API template variables from message content.

	Twilio Content API uses numbered variables (1, 2, 3...).
	These map to template placeholders like {{1}}, {{2}}, etc.
	"""
	# Generic variables — the actual template in Twilio defines
	# what {{1}}, {{2}}, etc. represent.
	return {
		"1": "Guest",
		"2": "Event",
		"3": "2026-12-31",
		"4": "12:00 PM",
		"5": "Venue",
		"6": frappe.utils.get_url() + "/rsvp",
	}


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

	frappe.publish_realtime(
		"refetch_resource",
		{"cache_key": "invite.api.notification.get_notifications"},
		user=frappe.session.user,
	)
