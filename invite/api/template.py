# Copyright (c) 2026, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe


@frappe.whitelist()
def get_list(filters=None, limit=100, offset=0):
	"""Get list of invitation templates."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = filters or {}

	templates = frappe.get_list(
		"Invitation Template",
		filters=base_filters,
		fields=[
			"name", "template_name", "title", "layout", "enabled", "is_default",
			"primary_color", "accent_color", "image_position", "qr_position",
			"invitation_message", "preview_image",
		],
		limit_start=offset,
		limit_page_length=limit,
		order_by="title ASC",
		ignore_permissions=True,
	)

	total = frappe.db.count("Invitation Template", base_filters)
	return {"templates": templates, "total": total}


@frappe.whitelist()
def get(template):
	"""Get a single template."""
	return frappe.get_doc("Invitation Template", template).as_dict()


@frappe.whitelist()
def create(data):
	"""Create a new invitation template."""
	if isinstance(data, str):
		data = json.loads(data)

	doc = frappe.new_doc("Invitation Template")
	doc.update(data)
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "template_name": doc.template_name}


@frappe.whitelist()
def update(template, data):
	"""Update an invitation template."""
	if isinstance(data, str):
		data = json.loads(data)

	doc = frappe.get_doc("Invitation Template", template)
	doc.update(data)
	doc.save(ignore_permissions=True)

	return {"name": doc.name, "template_name": doc.template_name}


@frappe.whitelist()
def delete(template):
	"""Delete an invitation template."""
	frappe.delete_doc("Invitation Template", template)
	return {"success": True}


@frappe.whitelist()
def get_options():
	"""Get lightweight template options for dropdowns (events, create flows)."""
	templates = frappe.get_all(
		"Invitation Template",
		filters={"enabled": 1},
		fields=["name", "title"],
		order_by="title ASC",
		ignore_permissions=True,
	)
	return {"templates": templates}