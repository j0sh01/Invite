import frappe


def execute():
	"""Seed four built-in invitation card templates if none exist yet."""
	if frappe.db.count("Invitation Template"):
		return

	templates = [
		{
			"template_name": "Classic Wedding",
			"title": "Classic Wedding",
			"layout": "Classic",
			"primary_color": "#8F3B1C",
			"accent_color": "#C9A227",
			"image_position": "Top",
			"qr_position": "Bottom Right",
			"invitation_message": (
				"Together with their families, {guest_name} is cordially invited to "
				"celebrate the wedding of {event_name}.\n\n"
				"{event_date} at {event_time} — {venue}"
			),
		},
		{
			"template_name": "Elegant Celebration",
			"title": "Elegant Celebration",
			"layout": "Elegant",
			"primary_color": "#1F3A5F",
			"accent_color": "#C9A227",
			"image_position": "Left",
			"qr_position": "Bottom Left",
			"invitation_message": (
				"Dear {guest_name},\n\nYou are cordially invited to {event_name} on "
				"{event_date} at {event_time}, {venue}."
			),
		},
		{
			"template_name": "Modern Party",
			"title": "Modern Party",
			"layout": "Modern",
			"primary_color": "#0F172A",
			"accent_color": "#C75F2C",
			"image_position": "Cover",
			"qr_position": "Top Right",
			"invitation_message": (
				"You're invited!\n\n{event_name} · {event_date} · {event_time}\n{venue}"
			),
		},
		{
			"template_name": "Minimal",
			"title": "Minimal",
			"layout": "Minimal",
			"primary_color": "#374151",
			"accent_color": "#8F3B1C",
			"image_position": "Top",
			"qr_position": "Bottom Left",
			"invitation_message": (
				"{guest_name}\n\nJoin us for {event_name}.\n{event_date} at {event_time} — {venue}"
			),
		},
	]

	for data in templates:
		doc = frappe.new_doc("Invitation Template")
		doc.update(data)
		doc.enabled = 1
		doc.is_default = 1 if data["template_name"] == "Classic Wedding" else 0
		doc.insert(ignore_permissions=True)

	frappe.db.commit()