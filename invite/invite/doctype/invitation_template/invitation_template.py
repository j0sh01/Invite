# Copyright (c) 2026, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class InvitationTemplate(Document):
	def validate(self):
		if self.is_default:
			# Only one template can be the default at a time
			frappe.db.sql(
				"UPDATE `tabInvitation Template` SET is_default = 0 "
				"WHERE is_default = 1 AND name != %s",
				self.name or "",
			)

	def on_trash(self):
		# Keep the template list clean: default flag only ever points at a live row
		pass