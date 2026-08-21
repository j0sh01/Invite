# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import csv
import io
import json

import frappe


@frappe.whitelist()
def get_list(event, filters=None, limit=50, offset=0):
	"""Get guests for an event."""
	if filters and isinstance(filters, str):
		filters = json.loads(filters)

	base_filters = {"event": event}
	if filters:
		base_filters.update(filters)

	guests = frappe.get_list("Guest",
		filters=base_filters,
		fields=["name", "full_name", "first_name", "last_name", "email", "mobile_no", "phone",
			"category", "plus_one", "plus_one_name",
			"rsvp_status", "rsvp_date", "number_of_attendees",
			"checked_in", "checked_in_at", "checked_in_by",
			"invitation_status", "invite_code", "qr_code", "invitation_sent_on"],
		limit_page_length=limit,
		limit_start=offset,
		order_by="creation ASC",
	)

	total = frappe.db.count("Guest", base_filters)

	return {"guests": guests, "total": total}


@frappe.whitelist()
def create(data):
	"""Create a new guest."""
	if isinstance(data, str):
		data = json.loads(data)

	guest = frappe.new_doc("Guest")
	guest.update(data)
	guest.insert(ignore_permissions=True)

	# Audit log
	try:
		from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
		log_action(
			event=guest.event,
			action_type="Guest Created",
			subject=f"Guest '{guest.full_name}' created",
			guest=guest.name,
			guest_name=guest.full_name,
			reference_doctype="Guest",
			reference_name=guest.name,
		)
	except Exception:
		pass

	return {"name": guest.name, "full_name": guest.full_name}


@frappe.whitelist()
def update(guest, data):
	"""Update a guest."""
	if isinstance(data, str):
		data = json.loads(data)

	guest_doc = frappe.get_doc("Guest", guest)
	guest_doc.update(data)
	guest_doc.save(ignore_permissions=True)

	# Audit log
	try:
		from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
		log_action(
			event=guest_doc.event,
			action_type="Guest Updated",
			subject=f"Guest '{guest_doc.full_name}' updated",
			guest=guest_doc.name,
			guest_name=guest_doc.full_name,
			reference_doctype="Guest",
			reference_name=guest_doc.name,
			extra_data={"updated_fields": list(data.keys())},
		)
	except Exception:
		pass

	return {"name": guest_doc.name, "full_name": guest_doc.full_name}


@frappe.whitelist()
def delete(guest):
	"""Delete a guest."""
	# Get info before deletion
	guest_info = frappe.db.get_value("Guest", guest, ["event", "full_name"], as_dict=True)

	frappe.delete_doc("Guest", guest)

	# Audit log
	if guest_info:
		try:
			from invite.invite.doctype.invite_activity_log.invite_activity_log import log_action
			log_action(
				event=guest_info.event,
				action_type="Guest Deleted",
				subject=f"Guest '{guest_info.full_name}' deleted",
				extra_data={"guest_name": guest_info.full_name},
			)
		except Exception:
			pass

	return {"success": True}


@frappe.whitelist()
def download_template():
	"""Download CSV template for guest import."""
	headers = [
		"First Name *", "Last Name", "Email", "Mobile No",
		"Category", "Number of Attendees", "Plus One (0/1)", "Plus One Name"
	]
	sample = [
		"John", "Doe", "john@example.com", "+255712345678",
		"Family", "1", "1", "Jane Doe"
	]

	frappe.response["doctype"] = "Guest"
	frappe.response["result"] = _generate_csv(headers, sample)
	frappe.response["type"] = "csv"


def _generate_csv(headers, sample_row=None):
	"""Generate CSV content with headers and optional sample data."""
	output = io.StringIO()
	writer = csv.writer(output)
	writer.writerow(headers)
	if sample_row:
		writer.writerow(sample_row)
	return output.getvalue()


def _sanitize_value(value, fieldname):
	"""Sanitize and validate a field value."""
	if value is None:
		return ""
	value = str(value).strip()

	# Boolean fields: normalize to "0" or "1"
	if fieldname in ("plus_one",):
		return "1" if value.lower() in ("yes", "true", "1", "y") else "0"

	return value


def _get_fieldnames(row):
	"""Map header row to standard field names, case-insensitively."""
	field_mappings = {
		"first name": "first_name", "firstname": "first_name",
		"last name": "last_name", "lastname": "last_name", "surname": "last_name",
		"email": "email", "e-mail": "email",
		"mobile": "mobile_no", "phone": "mobile_no", "telephone": "mobile_no",
		"mobile number": "mobile_no", "phone number": "mobile_no", "contact": "mobile_no",
		"category": "category", "guest category": "category",
		"number of attendees": "number_of_attendees", "attendees": "number_of_attendees",
		"plus one": "plus_one", "plusone": "plus_one", "+1": "plus_one",
		"plus one name": "plus_one_name", "plusone name": "plus_one_name",
	}
	result = []
	not_mapped = []
	for h in row:
		key = h.strip().lower().rstrip("*").strip()
		mapped = field_mappings.get(key)
		if mapped:
			result.append(mapped)
		else:
			result.append(key.replace(" ", "_"))
			not_mapped.append(h)
	return result, not_mapped


@frappe.whitelist()
def import_from_csv():
	"""Import guests from uploaded CSV file."""
	from frappe.utils.file_manager import get_file

	file_url = frappe.form_dict.get("file_url")
	event = frappe.form_dict.get("event")

	if not file_url or not event:
		frappe.throw("File URL and Event are required.")

	file_data = get_file(file_url)
	if isinstance(file_data, list) and len(file_data) >= 2:
		content = file_data[1]
	else:
		frappe.throw("Could not read uploaded file.")
	if isinstance(content, bytes):
		content = content.decode("utf-8-sig")
	reader = csv.DictReader(io.StringIO(content))

	fieldnames, unknown_columns = _get_fieldnames(reader.fieldnames or [])
	if unknown_columns:
		frappe.logger().warning(f"Unknown CSV columns mapped: {unknown_columns}")

	created = []
	errors = []
	row_num = 1

	for row in reader:
		row_num += 1
		try:
			guest_data = {}
			for i, fieldname in enumerate(fieldnames):
				raw_keys = list(row.keys())
				raw_key = raw_keys[i] if i < len(raw_keys) else ""
				val = row.get(raw_key, "")
				if val:
					guest_data[fieldname] = _sanitize_value(val, fieldname)

			if not guest_data.get("first_name"):
				errors.append({"row": row_num, "error": "First Name is required."})
				continue

			guest_data["event"] = event
			guest = frappe.new_doc("Guest")
			guest.update(guest_data)
			guest.insert(ignore_permissions=True)
			created.append(guest.name)
		except Exception as e:
			errors.append({"row": row_num, "error": str(e)})

	return {
		"created": created,
		"errors": errors,
		"total": len(created) + len(errors),
		"success_count": len(created),
		"error_count": len(errors),
	}
