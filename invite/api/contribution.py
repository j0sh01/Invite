# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import json

import frappe


def validate(doc, method=None):
	if not doc.recorded_by:
		doc.recorded_by = frappe.session.user


@frappe.whitelist()
def get_list(event, filters=None, limit=50, offset=0):
	"""Get contributions for an event."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = {"event": event}
	if filters:
		base_filters.update(filters)

	contributions = frappe.get_list("Contribution",
		filters=base_filters,
		fields=["name", "guest", "guest_name", "contribution_type", "type",
			"pledged_amount", "paid_amount", "outstanding_amount", "payment_status",
			"payment_method", "payment_date", "transaction_reference", "item_description",
			"currency", "notes"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="creation DESC",
	)

	total = frappe.db.count("Contribution", base_filters)

	return {"contributions": contributions, "total": total}


@frappe.whitelist()
def create(data):
	"""Create a new contribution."""
	if isinstance(data, str):
		data = json.loads(data)

	contrib = frappe.new_doc("Contribution")
	contrib.update(data)
	contrib.insert(ignore_permissions=True)

	return {"name": contrib.name, "message": "Contribution recorded successfully."}


@frappe.whitelist()
def update(contribution, data):
	"""Update a contribution."""
	if isinstance(data, str):
		data = json.loads(data)

	contrib_doc = frappe.get_doc("Contribution", contribution)
	contrib_doc.update(data)
	contrib_doc.save(ignore_permissions=True)

	return {"name": contrib_doc.name, "message": "Contribution updated successfully."}


@frappe.whitelist()
def delete(contribution):
	"""Delete a contribution."""
	frappe.delete_doc("Contribution", contribution)
	return {"success": True}


@frappe.whitelist()
def get_summary(event):
	"""Get contribution summary for an event."""
	return frappe.get_attr("invite.invite.doctype.contribution.contribution.get_contribution_summary")(event)
