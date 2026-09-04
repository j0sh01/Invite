# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.utils import get_url


# Built-in fallback used when an event has no template assigned and no
# template is marked as default in the system.
_BUILTIN_TEMPLATE = {
	"layout": "Classic",
	"primary_color": "#8F3B1C",
	"accent_color": "#C9A227",
	"image_position": "Top",
	"qr_position": "Bottom Right",
	"invitation_message": (
		"Together with their families, {guest_name} is cordially invited to "
		"{event_name}.\n\n{event_date} at {event_time} — {venue}"
	),
}


def _render_pdf(html, options):
	"""Render the invitation card HTML to a PDF via wkhtmltopdf.

	The card HTML is fully self-contained (inline CSS, base64 images, no
	print-format hooks), so it is rendered straight through wkhtmltopdf with
	the same options frappe's ``get_pdf`` would use.

	This intentionally bypasses ``frappe.utils.pdf.get_pdf``: that helper
	resolves the site's print bundle CSS via ``get_assets_json()``, which
	reads ``assets/assets.json`` relative to the process working directory.
	That manifest only exists under the bench's ``sites/`` folder, so card
	generation crashed with ``'NoneType' object has no attribute 'get'``
	whenever the code ran from any other directory (console scripts, RQ
	workers, freshly restarted bench processes).
	"""
	import pdfkit
	from packaging.version import Version
	from frappe.utils.pdf import get_wkhtmltopdf_version

	options = dict(options or {})
	options.update({
		"print-media-type": None,
		"background": None,
		"images": None,
		"quiet": None,
		"encoding": "UTF-8",
		"disable-javascript": "",
		"disable-local-file-access": "",
	})
	if Version(get_wkhtmltopdf_version()) > Version("0.12.3"):
		options["disable-smart-shrinking"] = ""

	return pdfkit.from_string(html, options=options, verbose=True)


@frappe.whitelist()
def generate_invitation_card(invitation):
	"""Generate a personalized invitation card PDF from the event's template.

	The card is a single A4 page designed from the event's selected
	Invitation Template (or the system default / built-in fallback):

	- The event image (the people the event is about — newlyweds, the
	  birthday star, etc.) is placed according to the template's image
	  position (Top / Left / Right / Cover).
	- The guest's own QR code is placed in the template's QR space.
	- The guest name and invitation wording are personalised per guest.

	Requires the event to have an image uploaded.
	"""
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
			"invite.invite.doctype.invitation.invitation.generate_qr_code"
		)(invitation)
		inv.reload()

	template = _get_event_template(event)
	html = _render_template_card_html(event, inv, template)

	# wkhtmltopdf does not honor @page margins from CSS, and frappe's get_pdf
	# defaults to 15mm side margins unless overridden — a 297mm-tall card then
	# overflows onto a second page. Pass explicit zero-margin A4 options so the
	# card is always exactly one page.
	pdf_content = _render_pdf(html, {
		"page-size": "A4",
		"margin-top": "0mm",
		"margin-bottom": "0mm",
		"margin-left": "0mm",
		"margin-right": "0mm",
		"orientation": "Portrait",
	})

	import os
	from frappe.utils import get_site_path

	filename = f"invitation_{inv.invite_code}.pdf"
	path = os.path.join(get_site_path("public", "files"), filename)
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "wb") as f:
		f.write(pdf_content)

	# Replace any previous card File record for this invitation (the PDF path
	# is deterministic per invite code, so regenerating must not stack
	# duplicate File docs)
	frappe.db.sql(
		"""DELETE FROM `tabFile`
		WHERE attached_to_doctype='Invitation' AND attached_to_name=%s
		AND file_url=%s""",
		(invitation, f"/files/{filename}"),
	)

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


def _get_event_template(event):
	"""Resolve the Invitation Template for an event.

	Precedence: event's assigned template > system default > built-in fallback.
	"""
	if event.invitation_template and frappe.db.exists("Invitation Template", event.invitation_template):
		return frappe.get_doc("Invitation Template", event.invitation_template)

	default = frappe.get_all(
		"Invitation Template",
		filters={"is_default": 1, "enabled": 1},
		fields=["name"],
		limit=1,
	)
	if default:
		return frappe.get_doc("Invitation Template", default[0].name)

	return frappe._dict(_BUILTIN_TEMPLATE)


def _render_template_card_html(event, inv, template):
	"""Build the single-page invitation card HTML from a template.

	Rendered with wkhtmltopdf (Qt WebKit), which has no ``object-fit`` and
	anchors absolute boxes to the page rather than the card when the card is
	not exactly one page tall. So everything is made explicit:

	- The card is exactly 297mm tall and overflow is hidden → always 1 page.
	- Event images are center-cropped server-side to the exact target box,
	  so no CSS object-fit is needed.
	- The QR block is placed with explicit mm ``top``/``left`` coordinates
	  computed from the template's QR position.
	"""
	base_url = get_url()
	# Images are embedded as base64 data URIs: wkhtmltopdf fetches remote
	# images with the site hostname (e.g. http://mchango:8000) which is not
	# resolvable inside the renderer on this setup — data URIs always work.
	qr_data_uri = _file_url_to_data_uri(inv.qr_code_image) if inv.qr_code_image else ""

	guest_name = inv.guest_name or "Valued Guest"
	layout = (template.get("layout") or "Classic").lower()
	image_position = (template.get("image_position") or "Top").lower()
	qr_position = (template.get("qr_position") or "Bottom Right").lower().replace(" ", "-")
	primary = template.get("primary_color") or "#8F3B1C"
	accent = template.get("accent_color") or "#C9A227"

	# Message with placeholders replaced, split into paragraphs
	message = template.get("invitation_message") or _BUILTIN_TEMPLATE["invitation_message"]
	event_date = frappe.utils.formatdate(event.event_date, "dd MMMM yyyy") if event.event_date else ""
	message = (
		message.replace("{guest_name}", guest_name)
		.replace("{event_name}", event.event_name or "our event")
		.replace("{event_date}", event_date)
		.replace("{event_time}", str(event.event_time or ""))
		.replace("{venue}", event.venue or "")
	)
	paragraphs = "".join(f"<p>{p.strip()}</p>" for p in message.split("\n\n") if p.strip())

	# Image block — cropped server-side to the exact mm box for this mode so
	# Qt WebKit never has to crop/cover it. Embedded as a data URI (see above).
	img_box_mm = _get_image_box_mm(layout, image_position)
	crop_data_uri = _crop_event_image(event.image, *img_box_mm) if event.image else ""
	if crop_data_uri:
		px_w = int(round(img_box_mm[0] * 3.78))
		px_h = int(round(img_box_mm[1] * 3.78))
		image_block = (
			f'<div class="people-image"><img class="people-img" src="{crop_data_uri}" '
			f'width="{px_w}" height="{px_h}" alt="Event image" /></div>'
		)
	else:
		image_block = '<div class="people-image people-image-empty"><span>Event photo</span></div>'

	# QR block
	if qr_data_uri:
		qr_block = (
			'<div class="qr-box" style="' + _qr_style(qr_position) + '">'
			f'<img class="qr-img" src="{qr_data_uri}" alt="QR code" />'
			'<div class="qr-caption">Scan to check in</div>'
			f'<div class="qr-code-text">{inv.invite_code}</div>'
			"</div>"
		)
	else:
		qr_block = '<div class="qr-box qr-box-empty" style="' + _qr_style(qr_position) + '"><span>QR code</span></div>'

	# Structural mode from image position
	mode = {
		"top": "mode-top",
		"left": "mode-side mode-side-left",
		"right": "mode-side mode-side-right",
		"cover": "mode-cover",
	}.get(image_position, "mode-top")

	# Overlay used only for cover-mode layouts so text stays readable
	overlay_block = '<div class="overlay"></div>' if mode == "mode-cover" else ""

	# Details row
	details_bits = [
		f'<span class="detail">{event_date}</span>' if event_date else "",
		f'<span class="detail">{str(event.event_time or "")}</span>' if event.event_time else "",
		f'<span class="detail">{event.venue or ""}</span>' if event.venue else "",
		f'<span class="detail">{event.location_address or ""}</span>' if event.location_address else "",
	]
	details_bits = [b for b in details_bits if b]
	details_html = (
		'<div class="event-details">' + " ".join(details_bits) + "</div>" if details_bits else ""
	)

	return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4 portrait; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: Georgia, 'Times New Roman', serif; color: #23252b; }}
.card {{ width: 210mm; height: 297mm; position: relative; overflow: hidden; background: #fffdf8; page-break-inside: avoid; }}

/* ---- Shared blocks ---- */
.people-image {{ overflow: hidden; }}
.people-img {{ display: block; }}
.people-image-empty {{ background: #f1ece2; color: #b6ad9c; text-align: center; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; }}
.people-image-empty span {{ position: relative; top: 50%; }}
.qr-box {{ position: absolute; width: 44mm; text-align: center; background: #ffffff; border: 1px solid #e5ddcd; padding: 5mm 4mm 4mm; }}
.qr-img {{ width: 30mm; height: 30mm; }}
.qr-caption {{ font-size: 8px; letter-spacing: 2px; text-transform: uppercase; margin-top: 2mm; }}
.qr-code-text {{ font-size: 9px; letter-spacing: 1px; margin-top: 1mm; font-family: monospace; }}
.qr-box-empty {{ padding: 16mm 0; color: #c3b9a6; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }}
.event-details {{ font-size: 13px; line-height: 1.9; }}
.event-details .detail {{ margin: 0 4px; }}

/* ---- Cover mode (any layout): full-page photo with readable text ---- */
.mode-cover .people-image {{ position: absolute; top: 0; left: 0; width: 210mm; height: 297mm; }}
.mode-cover .people-image-empty {{ background: #f1ece2; }}
.mode-cover .overlay {{ position: absolute; top: 0; left: 0; width: 210mm; height: 297mm; background: rgba(0, 0, 0, 0.58); }}
.mode-cover .content {{ position: absolute; top: 0; left: 0; width: 210mm; height: 297mm; padding: 44mm 26mm; }}
.mode-cover .guest-name {{ color: #ffffff !important; }}
.mode-cover .message {{ color: #f1f2f5 !important; }}
.mode-cover .event-details {{ color: #ffffff !important; }}
.mode-cover .eyebrow {{ color: #e9c46a !important; }}
.mode-cover .divider {{ border-color: rgba(255, 255, 255, 0.55); }}

/* ---- Side image mode (shared structural rules) ---- */
.mode-side .people-image {{ position: absolute; top: 0; height: 297mm; }}
.mode-side-left .people-image {{ left: 0; }}
.mode-side-right .people-image {{ right: 0; }}

/* ---- Classic: centered serif with ornamental frame ---- */
.layout-classic .card {{ border: 2.5px solid {primary}; }}
.layout-classic .content {{ padding: 14mm 26mm; text-align: center; }}
.layout-classic.mode-top .people-image {{ width: 210mm; height: 100mm; }}
.layout-classic.mode-side-left .people-image {{ width: 84mm; }}
.layout-classic.mode-side-right .people-image {{ width: 84mm; }}
.layout-classic.mode-side-left .content {{ padding-left: 104mm; text-align: left; }}
.layout-classic.mode-side-right .content {{ padding-right: 104mm; text-align: left; }}
.layout-classic .eyebrow {{ font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: {accent}; margin: 6mm 0 3mm; }}
.layout-classic .guest-name {{ font-size: 34px; color: {primary}; font-weight: normal; margin-bottom: 6mm; }}
.layout-classic .message {{ font-size: 14px; line-height: 1.8; color: #4b4d55; max-width: 130mm; margin: 0 auto; }}
.layout-classic .message p {{ margin-bottom: 3mm; }}
.layout-classic .event-details {{ margin-top: 8mm; color: {primary}; }}
.layout-classic .divider {{ width: 34mm; border-top: 1px solid {accent}; margin: 7mm auto; }}

/* ---- Elegant: navy & gold, side image ---- */
.layout-elegant .content {{ padding: 26mm 24mm; }}
.layout-elegant.mode-side-left .content {{ padding-left: 108mm; }}
.layout-elegant.mode-side-right .content {{ padding-right: 108mm; }}
.layout-elegant.mode-side-left .people-image {{ width: 88mm; }}
.layout-elegant.mode-side-right .people-image {{ width: 88mm; }}
.layout-elegant.mode-top .people-image {{ width: 210mm; height: 92mm; }}
.layout-elegant .eyebrow {{ font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: {accent}; margin-bottom: 5mm; }}
.layout-elegant .guest-name {{ font-size: 30px; color: {primary}; font-weight: normal; margin-bottom: 7mm; }}
.layout-elegant .message {{ font-size: 13px; line-height: 1.9; color: #55575f; }}
.layout-elegant .message p {{ margin-bottom: 3mm; }}
.layout-elegant .event-details {{ margin-top: 9mm; color: {primary}; }}
.layout-elegant .divider {{ width: 40mm; border-top: 2px solid {accent}; margin: 7mm 0; }}
.layout-elegant .qr-box {{ border-color: {accent}; }}

/* ---- Modern: dark card, sans-serif ---- */
.layout-modern .card {{ background: #0f172a; }}
.layout-modern .content {{ padding: 34mm 22mm; color: #ffffff; }}
.layout-modern.mode-top .people-image {{ width: 210mm; height: 88mm; }}
.layout-modern.mode-side-left .content {{ padding-left: 104mm; }}
.layout-modern.mode-side-right .content {{ padding-right: 104mm; }}
.layout-modern.mode-side-left .people-image {{ width: 84mm; }}
.layout-modern.mode-side-right .people-image {{ width: 84mm; }}
.layout-modern .eyebrow {{ font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: {accent}; margin-bottom: 5mm; }}
.layout-modern .guest-name {{ font-family: Helvetica, Arial, sans-serif; font-size: 38px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8mm; }}
.layout-modern .message {{ font-family: Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.8; color: #e8eaf0; }}
.layout-modern .message p {{ margin-bottom: 3mm; }}
.layout-modern .event-details {{ margin-top: 10mm; font-family: Helvetica, Arial, sans-serif; color: {accent}; }}
.layout-modern .qr-box {{ border-color: rgba(255, 255, 255, 0.35); background: rgba(255, 255, 255, 0.92); }}

/* ---- Minimal: whitespace, thin rules ---- */
.layout-minimal .card {{ background: #ffffff; }}
.layout-minimal .content {{ padding: 20mm 30mm; text-align: center; }}
.layout-minimal.mode-top .people-image {{ width: 110mm; height: 70mm; margin: 0 auto; }}
.layout-minimal.mode-side-left .content {{ padding-left: 100mm; text-align: left; }}
.layout-minimal.mode-side-right .content {{ padding-right: 100mm; text-align: left; }}
.layout-minimal.mode-side-left .people-image {{ width: 80mm; }}
.layout-minimal.mode-side-right .people-image {{ width: 80mm; }}
.layout-minimal .eyebrow {{ font-size: 9px; letter-spacing: 5px; text-transform: uppercase; color: #9aa0a8; margin: 8mm 0 4mm; }}
.layout-minimal .guest-name {{ font-family: Helvetica, Arial, sans-serif; font-size: 32px; font-weight: 300; color: #26272b; margin-bottom: 7mm; }}
.layout-minimal .message {{ font-size: 13px; line-height: 2; color: #6b6f76; }}
.layout-minimal .message p {{ margin-bottom: 3mm; }}
.layout-minimal .event-details {{ margin-top: 9mm; color: #26272b; }}
.layout-minimal .divider {{ width: 26mm; border-top: 1px solid #d9dce1; margin: 7mm auto; }}
</style>
</head>
<body>	<div class="card layout-{layout} {mode}">
	{image_block}
	{overlay_block}
	<div class="content">
		<div class="eyebrow">You are cordially invited</div>
		<h1 class="guest-name">{guest_name}</h1>
		<div class="divider"></div>
		<div class="message">{paragraphs}</div>
		{details_html}
	</div>
	{qr_block}
</div>
<!-- Empty header/footer hooks: frappe's prepare_header_footer() forces
15mm top/bottom margins when these are absent — with them present (empty),
margins stay 0 and the 297mm card fits exactly one A4 page. -->
<div id="header-html"></div>
<div id="footer-html"></div>
</body>
</html>"""


def _get_image_box_mm(layout, image_position):
	"""Return (width_mm, height_mm) of the image box for a layout + position."""
	layout = layout or "classic"
	position = image_position or "top"
	# (width, height) in mm for each layout × image position
	boxes = {
		"classic": {"top": (210, 100), "left": (84, 297), "right": (84, 297), "cover": (210, 297)},
		"elegant": {"top": (210, 92), "left": (88, 297), "right": (88, 297), "cover": (210, 297)},
		"modern": {"top": (210, 88), "left": (84, 297), "right": (84, 297), "cover": (210, 297)},
		"minimal": {"top": (110, 70), "left": (80, 297), "right": (80, 297), "cover": (210, 297)},
	}
	return boxes.get(layout, boxes["classic"]).get(position, (210, 100))


def _crop_event_image(image_url, width_mm, height_mm):
	"""Center-crop + resize the event image to an exact box.

	Qt WebKit (wkhtmltopdf) does not support ``object-fit: cover``, so the
	image is cropped server-side to exactly the target aspect ratio and saved
	as a cached JPEG in /files/_card_crops/. Returns a base64 data URI (so
	wkhtmltopdf never needs to fetch the image over the network), or "" if
	the image could not be processed.
	"""
	import base64
	import hashlib
	import io
	import os

	from PIL import Image
	from frappe.utils import get_site_path
	from frappe.utils.file_manager import get_file

	if not image_url:
		return ""

	px_w = max(1, int(round(width_mm * 3.78)))
	px_h = max(1, int(round(height_mm * 3.78)))

	# Cache by (image, box)
	key = hashlib.md5(f"{image_url}:{px_w}x{px_h}".encode()).hexdigest()[:16]
	abspath = os.path.join(get_site_path("public", "files", "_card_crops"), f"card_{key}.jpg")

	if os.path.exists(abspath):
		return _jpeg_data_uri(abspath)

	try:
		# frappe.utils.file_manager.get_file returns [filename, content]
		_filename, content = get_file(image_url)
		img = Image.open(io.BytesIO(content))
		img = img.convert("RGB")
	except Exception:
		frappe.log_error(f"Failed to load event image {image_url} for card", "Invitation Card")
		return ""

	# Center-crop to the target aspect ratio, then resize to exact px
	src_w, src_h = img.size
	target_ratio = px_w / px_h
	src_ratio = src_w / src_h
	if src_ratio > target_ratio:
		new_w = int(src_h * target_ratio)
		left = (src_w - new_w) // 2
		img = img.crop((left, 0, left + new_w, src_h))
	else:
		new_h = int(src_w / target_ratio)
		top = (src_h - new_h) // 2
		img = img.crop((0, top, src_w, top + new_h))
	img = img.resize((px_w, px_h), Image.LANCZOS)

	try:
		os.makedirs(os.path.dirname(abspath), exist_ok=True)
		img.save(abspath, "JPEG", quality=88)
	except Exception:
		frappe.log_error(f"Failed to save card crop for {image_url}", "Invitation Card")
		return ""

	return _jpeg_data_uri(abspath)


def _jpeg_data_uri(abspath):
	"""Base64 data URI for a JPEG file on disk."""
	import base64
	with open(abspath, "rb") as f:
		return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def _file_url_to_data_uri(file_url):
	"""Return a base64 data URI for a file referenced by a /files/... URL."""
	import base64
	import mimetypes

	if not file_url:
		return ""
	mime = mimetypes.guess_type(file_url.split("?")[0])[0] or "image/png"
	try:
		from frappe.utils.file_manager import get_file
		_filename, content = get_file(file_url)
	except Exception:
		frappe.log_error(f"Failed to read {file_url} for card image", "Invitation Card")
		return ""
	return f"data:{mime};base64," + base64.b64encode(content).decode()


def _qr_style(qr_position):
	"""Return the inline CSS (mm coordinates) for a QR position.

	Qt WebKit anchors ``bottom``/``right`` to the page rather than the card,
	so the QR box is positioned with explicit ``top``/``left`` computed from
	the A4 card size (210×297mm) and the QR box footprint (~44×46mm).
	"""
	card_w, card_h = 210, 297
	box_w, box_h = 44, 46
	margin = 13
	positions = {
		"bottom-right": (card_h - margin - box_h, card_w - margin - box_w),
		"bottom-left": (card_h - margin - box_h, margin),
		"top-right": (margin, card_w - margin - box_w),
		"side-right": ((card_h - box_h) / 2, card_w - 8 - box_w),
	}
	top, left = positions.get(qr_position, positions["bottom-right"])
	return f"top: {top:.1f}mm; left: {left:.1f}mm;"


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
	"""Send event reminders with RSVP link (and card when one exists).

	A guest is only reported as sent when the provider actually accepted the
	message - failures are listed with a reason instead of silently counted.
	"""
	guests = frappe.get_all(
		"Guest",
		filters={"event": event_doc.name},
		fields=["name", "full_name", "email", "mobile_no", "invite_code"],
	)

	base_url = get_url()
	sent = []
	failed = []

	for guest in guests:
		try:
			rsvp_link = f"{base_url}/rsvp?code={guest.invite_code}" if guest.invite_code else ""
			message = (
				f"Dear {guest.full_name or 'Guest'},\n\n"
				f"This is a reminder that {event_doc.event_name} is on "
				f"{event_doc.event_date} at {event_doc.venue}.\n\n"
				f"Please RSVP here: {rsvp_link}"
			)

			# Attach the personalized card when one has already been generated
			card_path = frappe.db.get_value(
				"Invitation",
				{"event": event_doc.name, "guest": guest.name},
				"personalized_invite_card",
			)

			sent_channels, send_failures = _dispatch_to_guest(
				guest=guest,
				event_doc=event_doc,
				message=message,
				subject=f"Reminder: {event_doc.event_name}",
				channel=channel,
				attachment_path=card_path,
				template_type="event_reminder",
				rsvp_link=rsvp_link,
			)
			failed.extend(send_failures)
			for sc in sent_channels:
				sent.append({"guest": guest.name, "channel": sc})
			if sent_channels:
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
	"""Send thank you messages to every guest who checked in (once per guest)."""
	# Deduplicate: a card covering multiple attendees can be scanned several
	# times, but each guest should receive exactly one thank-you message.
	checked_in_rows = frappe.get_all(
		"Check-In",
		filters={"event": event_doc.name, "is_duplicate": 0},
		fields=["guest"],
		group_by="guest",
	)
	guest_ids = [r["guest"] for r in checked_in_rows]
	guests = frappe.get_all(
		"Guest",
		filters={"name": ["in", guest_ids]},
		fields=["name", "full_name", "email", "mobile_no"],
	) if guest_ids else []

	sent = []
	failed = []

	for guest in guests:
		try:
			message = (
				f"Dear {guest.full_name or 'Guest'},\n\n"
				f"Thank you for attending {event_doc.event_name}! "
				"We truly appreciate your presence and hope you had a wonderful time."
			)

			sent_channels, send_failures = _dispatch_to_guest(
				guest=guest,
				event_doc=event_doc,
				message=message,
				subject=f"Thank You: {event_doc.event_name}",
				channel=channel,
				attachment_path=event_doc.image or "",
				template_type="thank_you",
			)
			failed.extend(send_failures)
			for sc in sent_channels:
				sent.append({"guest": guest.name, "channel": sc})
			if sent_channels:
				_log_notification(guest, event_doc, f"Thank you for joining {event_doc.event_name}!")

		except Exception as e:
			failed.append({"guest": guest.name, "error": str(e)})
			frappe.log_error(
				f"Thank you message failed for {guest.name}: {frappe.get_traceback()}",
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


def _dispatch_to_guest(guest, event_doc, message, subject, channel,
	attachment_path=None, template_type=None, rsvp_link=None):
	"""Send one message to one guest over the requested channel.

	``guest`` is a dict with ``name``/``full_name``/``email``/``mobile_no``.

	Returns ``(sent_channels, failures)`` — the channels the provider actually
	accepted ("Email"/"WhatsApp") and any per-guest failures with a reason,
	so callers never count a message as sent when nothing was dispatched.
	"""
	sent_channels = []
	failures = []
	template_values = None
	if template_type and guest.get("full_name"):
		template_values = _template_values(guest.get("full_name"), event_doc, rsvp_link)

	if channel in (None, "Email"):
		if guest.get("email"):
			if _send_email(guest["email"], subject, message, attachment_path):
				sent_channels.append("Email")
			else:
				failures.append({"guest": guest.get("name"), "error": "Email could not be queued (check outbound email settings)"})
		elif channel == "Email":
			failures.append({"guest": guest.get("name"), "error": "Guest has no email address"})

	if channel in (None, "WhatsApp"):
		if guest.get("mobile_no"):
			if _send_whatsapp(
				guest["mobile_no"],
				message,
				attachment_url=attachment_path,
				event_name=event_doc.name,
				template_type=template_type,
				template_values=template_values,
			):
				sent_channels.append("WhatsApp")
			else:
				provider = getattr(frappe.get_single("Event Settings"), "whatsapp_provider", "")
				reason = "WhatsApp provider did not deliver the message"
				if provider == "Twilio":
					reason += (
						" (Twilio accepted it but the recipient could not receive it - "
						"e.g. the number has not joined the WhatsApp sandbox)"
					)
				failures.append({"guest": guest.get("name"), "error": reason})
		elif channel == "WhatsApp":
			failures.append({"guest": guest.get("name"), "error": "Guest has no mobile number"})

	return sent_channels, failures


def _template_values(guest_name, event_doc, rsvp_link=None):
	"""Numbered (1-6) values for Twilio Content API templates.

	The send helper maps these positionally onto the template's own named
	variables and refuses to send when the template expects a different
	number of variables, so a mismatched template falls back to plain text
	instead of delivering wrong content.
	"""
	return {
		"1": guest_name or "Guest",
		"2": event_doc.event_name or "",
		"3": str(event_doc.event_date or ""),
		"4": str(event_doc.event_time or ""),
		"5": event_doc.venue or "",
		"6": rsvp_link or "",
	}


def _send_email(recipient, subject, message, attachment_path=None):
	"""Queue an email with optional attachment (file URL).

	Returns True when the email was accepted into the outbound queue (it is
	then delivered by Frappe's email queue, which requires an outgoing email
	account to be configured on the site).
	"""
	import json
	from frappe.email.doctype.email_queue.email_queue import EmailQueue

	if not recipient:
		return False

	try:
		email_queue = EmailQueue.new({
			"sender": frappe.session.user,
			"recipients": [recipient],
			"subject": subject,
			"message": message,
			"reference_doctype": "Event",
		}, ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Failed to queue email to {recipient}: {e}", "Send Email")
		return False

	if email_queue and attachment_path:
		try:
			attachments = json.loads(email_queue.attachments) if email_queue.attachments else []
			attachments.append({"file_url": attachment_path})
			email_queue.db_set("attachments", json.dumps(attachments))
		except Exception as e:
			frappe.log_error(f"Failed to attach file to email: {e}", "Send Email")

	return True


def _send_whatsapp(mobile_no, message, attachment_url=None, event_name=None,
	template_type=None, template_values=None):
	"""Send a WhatsApp message via the configured provider.

	Returns True only when the provider actually accepted the message:

	- Twilio: the Content API template for ``template_type`` is tried first
	  when a SID is configured. If the template send fails (wrong variable
	  count, not approved, sandbox restrictions) it falls back to plain
	  text. The card is attached only when its URL is publicly reachable by
	  Twilio (never for local-only hosts like ``http://mchango:8000``).
	- Official WhatsApp API: media message first, plain text fallback.
	"""
	mobile = str(mobile_no or "").strip()
	if not mobile:
		return False

	settings = frappe.get_single("Event Settings")
	provider = getattr(settings, "whatsapp_provider", "")

	if provider == "Twilio":
		from invite.api.twilio import (
			send_whatsapp_message,
			send_template_message,
			get_template_sids,
			_is_publicly_reachable_url,
		)

		template_sid = ""
		if template_type:
			template_sid = (get_template_sids().get(template_type) or "")
		if template_sid and send_template_message(mobile, template_sid, template_values or {}):
			return True

		# Plain-text fallback; attach media only when Twilio can fetch it
		media_url = None
		if attachment_url:
			full_url = attachment_url if attachment_url.startswith("http") else frappe.utils.get_url(attachment_url)
			if _is_publicly_reachable_url(full_url):
				media_url = full_url
		return send_whatsapp_message(mobile, message, media_url=media_url)

	if provider in ("Official WhatsApp API", "Meta API"):
		from invite.api.whatsapp import send_text_message, send_media_message
		if attachment_url:
			ok, _err = send_media_message(mobile, message, attachment_url)
			if ok:
				return True
		return send_text_message(mobile, message)

	frappe.log_error(
		f"WhatsApp send skipped for {mobile}: whatsapp_provider is '{provider}'",
		"Send Communication",
	)
	return False


def _log_notification(guest, event_doc, subject):
	"""Log a notification for audit trail and push real-time update.

	Accepts both Guest documents and plain dicts (as returned by get_all).
	"""
	if isinstance(guest, dict):
		contact = str(guest.get("email") or guest.get("mobile_no") or "").strip() or "unknown"
	else:
		contact = str(getattr(guest, "email", "") or getattr(guest, "mobile_no", "") or "").strip() or "unknown"

	frappe.get_doc({
		"doctype": "Notification Log",
		"subject": subject,
		"email": contact,
		"for_user": frappe.session.user,
		"document_type": "Event",
		"document_name": event_doc.name,
	}).insert(ignore_permissions=True)

	frappe.publish_realtime(
		"refetch_resource",
		{"cache_key": "invite.api.notification.get_notifications"},
		user=frappe.session.user,
	)
