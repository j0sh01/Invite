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

	The frontdesk_role is configured in Event Settings. Any user who has
	that role is treated as a frontdesk user — regardless of whether they
	also hold other roles like System Manager or Event Manager.

	The Administrator is the one exception: frappe.get_roles() resolves
	EVERY role in the system for the Administrator (see
	frappe.permissions.get_roles), not just the roles explicitly assigned
	to the account. Without this exception an Administrator would always
	match the configured frontdesk role and get locked out of the normal
	dashboard.

	Returns:
	    frontdesk_role: the role configured in Event Settings (or empty)
	    user_roles: list of roles the current user has
	    is_frontdesk_only: True if the configured frontdesk role exists
	                        and the current user has it
	"""
	settings = frappe.get_single("Event Settings")
	frontdesk_role = getattr(settings, "frontdesk_role", "") or ""
	user = frappe.session.user
	user_roles = frappe.get_roles()

	# Administrator implicitly resolves to all roles, so only redirect when
	# the frontdesk role is genuinely assigned to a non-Administrator user.
	is_frontdesk_only = (
		bool(frontdesk_role)
		and user != "Administrator"
		and frontdesk_role in user_roles
	)

	return {
		"frontdesk_role": frontdesk_role,
		"user_roles": user_roles,
		"is_frontdesk_only": is_frontdesk_only,
	}
