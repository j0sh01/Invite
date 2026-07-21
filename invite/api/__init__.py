# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import frappe
from frappe.translate import get_all_translations
from frappe.utils import cstr


@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")

	return get_all_translations(language)


def check_app_permission():
	"""Check if user has permission to access the invite app."""
	if frappe.session.user == "Administrator":
		return True

	from frappe.config import get_modules_from_all_apps_for_user
	allowed_modules = get_modules_from_all_apps_for_user()
	allowed_modules = [x["module_name"] for x in allowed_modules]

	if "Invite" not in allowed_modules:
		return False

	roles = frappe.get_roles()
	if any(role in ["System Manager", "Event Manager"] for role in roles):
		return True

	return False
