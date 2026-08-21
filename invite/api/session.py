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


@frappe.whitelist()
def get_user_role_info():
	"""Return role info needed for frontdesk redirect logic.

	Returns:
	    frontdesk_role: the role configured in Event Settings (or empty)
	    user_roles: list of roles the current user has
	    is_frontdesk_only: True if user has the frontdesk role but none
	                        of the normal app roles (System Manager,
	                        Event Manager)
	"""
	settings = frappe.get_single("Event Settings")
	frontdesk_role = getattr(settings, "frontdesk_role", "") or ""
	user_roles = frappe.get_roles()

	# Normal app roles that should see the full dashboard
	app_roles = {"System Manager", "Event Manager"}
	is_frontdesk_only = bool(frontdesk_role) and frontdesk_role in user_roles and not (app_roles & set(user_roles))

	return {
		"frontdesk_role": frontdesk_role,
		"user_roles": user_roles,
		"is_frontdesk_only": is_frontdesk_only,
	}
