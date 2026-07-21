import frappe


def execute():
	"""Recalculate contribution summaries for all guests with contributions.
	Uses db.set_value to avoid triggering hooks (Event.validate_dates can fail on past events).
	"""
	guests_with_contributions = frappe.db.get_all(
		"Contribution",
		fields=["guest"],
		distinct=True,
		filters={"docstatus": 0},
		pluck="guest",
	)

	for guest_name in guests_with_contributions:
		contributions = frappe.get_all(
			"Contribution",
			filters={"guest": guest_name, "docstatus": 0},
			fields=[
				"sum(pledged_amount) as total_pledged",
				"sum(paid_amount) as total_paid",
			],
		)
		if contributions:
			pledged = contributions[0].total_pledged or 0
			paid = contributions[0].total_paid or 0
			outstanding = pledged - paid
			frappe.db.set_value(
				"Guest",
				guest_name,
				{
					"pledge_amount": pledged,
					"paid_amount": paid,
					"outstanding_amount": outstanding,
				},
			)
			print(f"Updated {guest_name}: pledged={pledged}, paid={paid}, outstanding={outstanding}")

	print(f"Fixed {len(guests_with_contributions)} guests")
