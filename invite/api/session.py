# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe


@frappe.whitelist()
def get_logged_user(**kwargs):
	"""Get currently logged in user info."""
	return frappe.session.user


@frappe.whitelist()
def get_current_user_info(**kwargs):
	"""Get current logged in user's display info."""
	user = frappe.session.user
	full_name = frappe.db.get_value("User", user, "full_name")
	return {
		"user": user,
		"full_name": full_name or user,
	}
