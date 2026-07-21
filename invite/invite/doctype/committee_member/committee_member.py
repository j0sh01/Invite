# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommitteeMember(Document):
	def validate(self):
		self.set_permissions_by_role()
		self.validate_unique_member()

	def set_permissions_by_role(self):
		"""Set default permissions based on role."""
		if self.role == "Organizer":
			self.can_invite = 1
			self.can_check_in = 1
			self.can_manage_guests = 1
			self.can_manage_contributions = 1
			self.can_view_reports = 1
		elif self.role == "Treasurer":
			self.can_manage_contributions = 1
			self.can_view_reports = 1
		elif self.role == "Usher":
			self.can_check_in = 1
		elif self.role == "Invitation Coordinator":
			self.can_invite = 1
			self.can_manage_guests = 1

	def validate_unique_member(self):
		"""Ensure no duplicate committee members."""
		existing = frappe.db.get_value(
			"Committee Member",
			{"event": self.event, "user": self.user, "name": ["!=", self.name]},
			"name",
		)
		if existing:
			frappe.throw(f"User {self.user} is already a committee member for this event.")


@frappe.whitelist()
def get_event_committee(event, **kwargs):
	"""Get committee members for an event."""
	return frappe.get_all(
		"Committee Member",
		filters={"event": event, "is_active": 1},
		fields=["name", "user", "user_name", "role", "can_invite", "can_check_in",
				"can_manage_guests", "can_manage_contributions", "can_view_reports"],
		order_by="role ASC",
	)
