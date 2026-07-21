# Copyright (c) 2024, Joshua Michael and Contributors
# MIT License. See license.txt
import frappe


def before_uninstall():
	"""Clean up app-specific data before uninstall."""
	# Remove all app-specific doctypes
	doctypes = [
		"Event",
		"Guest",
		"Invitation",
		"RSVP",
		"Contribution",
		"Check-In",
		"Committee Member",
		"Event Settings",
		"Event Type",
		"Event Status",
		"Guest Category",
		"Contribution Type",
		"RSVP Status",
	]

	for doctype in doctypes:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True)
