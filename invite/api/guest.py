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
		fields=["name", "full_name", "first_name", "last_name", "email", "mobile_no",
			"category", "rsvp_status", "checked_in", "pledge_amount", "paid_amount",
			"outstanding_amount", "invitation_status", "guest_type", "number_of_attendees",
			"invite_code", "qr_code", "notes"],
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

	return {"name": guest.name, "full_name": guest.full_name}


@frappe.whitelist()
def update(guest, data):
	"""Update a guest."""
	if isinstance(data, str):
		data = json.loads(data)

	guest_doc = frappe.get_doc("Guest", guest)
	guest_doc.update(data)
	guest_doc.save(ignore_permissions=True)

	return {"name": guest_doc.name, "full_name": guest_doc.full_name}


@frappe.whitelist()
def delete(guest):
	"""Delete a guest."""
	frappe.delete_doc("Guest", guest)
	return {"success": True}


@frappe.whitelist()
def download_template():
	"""Download CSV template for guest import."""
	headers = [
		"First Name *", "Last Name", "Email", "Mobile No",
		"Category", "Guest Type", "Plus One (0/1)", "Plus One Name", "Notes"
	]
	sample = [
		"John", "Doe", "john@example.com", "+255712345678",
		"Family", "Individual", "1", "Jane Doe", "VIP guest"
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
	"""Sanitize and validate a field value.
	Fieldname is already mapped by _get_fieldnames, so just handle special types."""
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
		"guest type": "guest_type", "type": "guest_type",
		"plus one": "plus_one", "plusone": "plus_one", "+1": "plus_one",
		"plus one name": "plus_one_name", "plusone name": "plus_one_name",
		"notes": "notes", "note": "notes", "remarks": "notes", "comment": "notes",
	}
	result = []
	not_mapped = []
	for h in row:
		# Strip special markers like * for required fields
		key = h.strip().lower().rstrip("*").strip()
		mapped = field_mappings.get(key)
		if mapped:
			result.append(mapped)
		else:
			# Keep original but lowercase and underscore
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
	# get_file returns [filename, content_bytes]
	if isinstance(file_data, list) and len(file_data) >= 2:
		content = file_data[1]
	else:
		frappe.throw("Could not read uploaded file.")
	if isinstance(content, bytes):
		content = content.decode("utf-8-sig")
	reader = csv.DictReader(io.StringIO(content))

	# Get mapped fieldnames
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
