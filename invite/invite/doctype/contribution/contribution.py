# Copyright (c) 2024, Joshua Michael and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Contribution(Document):
	def validate(self):
		self.calculate_outstanding()
		self.set_currency()
		self.set_recorded_by()

	def on_update(self):
		"""After DB is updated, sync guest summary."""
		self.update_guest_contribution()

	def calculate_outstanding(self):
		pledged = float(self.pledged_amount or 0)
		paid = float(self.paid_amount or 0)
		self.outstanding_amount = pledged - paid

		if paid >= pledged and pledged > 0:
			self.payment_status = "Paid"
		elif paid > 0:
			self.payment_status = "Partially Paid"

	def set_currency(self):
		if not self.currency:
			event = frappe.get_cached_doc("Event", self.event)
			self.currency = event.currency or "TZS"

	def set_recorded_by(self):
		if not self.recorded_by:
			self.recorded_by = frappe.session.user

	def update_guest_contribution(self):
		"""Update guest's contribution summary fields."""
		if self.guest:
			guest = frappe.get_doc("Guest", self.guest)
			contributions = frappe.get_all(
				"Contribution",
				filters={"guest": self.guest, "docstatus": 0},
				fields=["sum(pledged_amount) as total_pledged", "sum(paid_amount) as total_paid"],
			)
			if contributions:
				guest.pledge_amount = contributions[0].total_pledged or 0
				guest.paid_amount = contributions[0].total_paid or 0
				guest.outstanding_amount = (contributions[0].total_pledged or 0) - (contributions[0].total_paid or 0)
				guest.save(ignore_permissions=True)


@frappe.whitelist()
def get_contribution_summary(event):
	"""Get contribution summary for an event."""
	contributions = frappe.get_all(
		"Contribution",
		filters={"event": event},
		fields=["name", "pledged_amount", "paid_amount", "outstanding_amount", "contribution_type", "payment_status"],
	)

	total_pledged = sum(c.pledged_amount or 0 for c in contributions)
	total_paid = sum(c.paid_amount or 0 for c in contributions)
	total_outstanding = sum(c.outstanding_amount or 0 for c in contributions)

	# By type
	type_summary = {}
	for c in contributions:
		ctype = c.contribution_type or "Other"
		if ctype not in type_summary:
			type_summary[ctype] = {"pledged": 0, "paid": 0, "count": 0}
		type_summary[ctype]["pledged"] += c.pledged_amount or 0
		type_summary[ctype]["paid"] += c.paid_amount or 0
		type_summary[ctype]["count"] += 1

	return {
		"total_contributions": len(contributions),
		"total_pledged": total_pledged,
		"total_paid": total_paid,
		"total_outstanding": total_outstanding,
		"collection_rate": round(total_paid / total_pledged * 100, 1) if total_pledged > 0 else 0,
		"by_type": type_summary,
	}


@frappe.whitelist()
def reconcile_contribution(contribution, paid_amount, payment_method=None, transaction_reference=None):
	"""Record a payment against a pledge."""
	contrib = frappe.get_doc("Contribution", contribution)
	contrib.paid_amount = (contrib.paid_amount or 0) + float(paid_amount)
	contrib.type = "Partial Payment" if contrib.paid_amount < contrib.pledged_amount else "Payment"
	contrib.payment_date = frappe.utils.nowdate()
	if payment_method:
		contrib.payment_method = payment_method
	if transaction_reference:
		contrib.transaction_reference = transaction_reference
	contrib.save(ignore_permissions=True)

	return {"success": True, "outstanding": contrib.outstanding_amount}
