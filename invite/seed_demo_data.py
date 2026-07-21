"""
Seed Demo Data for Invite App
Creates 5 events with related guests, invitations, contributions, RSVPs, check-ins, and committee members.
Run with: bench --site mchango execute invite.seed_demo_data.seed_demo_data
"""

import frappe
from frappe.utils import today, add_days, add_years, now_datetime, getdate
from random import randint, choice, uniform
from datetime import time
from invite.install import (
	add_default_event_types,
	add_default_event_statuses,
	add_default_guest_categories,
	add_default_contribution_types,
	add_default_rsvp_statuses,
)


def seed_demo_data():
	"""Create demo data for all 5 events."""
	print("🌱 Seeding demo data...")
	
	_clear_existing_demo_data()
	
	# Ensure all reference data exists (idempotent - skips existing)
	print("   Ensuring reference data exists...")
	add_default_event_types()
	add_default_event_statuses()
	add_default_guest_categories()
	add_default_contribution_types()
	add_default_rsvp_statuses()
	frappe.db.commit()
	
	# Create 5 events (all with today or future dates to pass validation)
	wedding = _create_event("John & Mary's Wedding", "Wedding", "Completed", 0, "10:00", 
		"St. Joseph's Cathedral, Dar es Salaam", "John Michael", "+255 712 345 678", "john@example.com", 200)
	
	fundraiser = _create_event("Annual Church Fundraiser", "Church Event", "Ongoing", 5, "14:00",
		"City Community Center", "Pastor James", "+255 713 456 789", "church@example.com", 300)
	
	graduation = _create_event("Sarah's Graduation Party", "Graduation", "Planning", 45, "16:00",
		"KiliGrid Gardens", "Peter Mwangi", "+255 714 567 890", "peter@example.com", 80)
	
	birthday = _create_event("Grandma's 80th Birthday", "Birthday", "Invitations Sent", 14, "12:00",
		"Family Homestead, Arusha", "Grace Kimaro", "+255 715 678 901", "grace@example.com", 100)
	
	conference = _create_event("City Business Conference", "Corporate Event", "RSVPs Open", 21, "08:00",
		"Dar es Salaam Convention Center", "CEO Roundtable", "+255 716 789 012", "info@ceo.co.tz", 500)
	
	# Create guests for each event
	wedding_guests = _create_wedding_guests(wedding)
	fundraiser_guests = _create_fundraiser_guests(fundraiser)
	graduation_guests = _create_graduation_guests(graduation)
	birthday_guests = _create_birthday_guests(birthday)
	conference_guests = _create_conference_guests(conference)
	
	# Create invitations
	wedding_invites = _create_invitations(wedding, wedding_guests, "Digital", "WhatsApp")
	fundraiser_invites = _create_invitations(fundraiser, fundraiser_guests, "Digital", "SMS")
	graduation_invites = _create_invitations(graduation, graduation_guests, "Digital", "WhatsApp")
	birthday_invites = _create_invitations(birthday, birthday_guests, "Digital", "WhatsApp")
	conference_invites = _create_invitations(conference, conference_guests, "Digital", "Email")
	
	# Create RSVPs
	_create_rsvps(wedding, wedding_guests[:6], wedding_invites[:6], "Accepted", 2)
	_create_rsvps(wedding, wedding_guests[6:8], wedding_invites[6:8], "Declined", 0)
	_create_rsvps(fundraiser, fundraiser_guests[:3], fundraiser_invites[:3], "Accepted", 1)
	_create_rsvps(birthday, birthday_guests[:4], birthday_invites[:4], "Accepted", 3)
	_create_rsvps(conference, conference_guests[:5], conference_invites[:5], "Accepted", 1)
	
	# Create contributions
	_create_contributions(wedding, wedding_guests, [
		("Cash Contribution", 500000, 500000, "Paid", "Mobile Money", "TRX-WED-001"),
		("Cash Contribution", 300000, 300000, "Paid", "Cash", None),
		("In-Kind Contribution", 200000, 200000, "Paid", "In-Kind", None),
		("Cash Contribution", 1000000, 500000, "Partially Paid", "Mobile Money", "TRX-WED-002"),
		("Cash Contribution", 150000, 150000, "Paid", "Cash", None),
		("Cash Contribution", 250000, 0, "Pending", None, None),
		("Mobile Money", 800000, 800000, "Paid", "Mobile Money", "TRX-WED-003"),
		("Cash Contribution", 100000, 100000, "Paid", "Cash", None),
	])
	
	_create_contributions(fundraiser, fundraiser_guests, [
		("Cash Contribution", 200000, 200000, "Paid", "Cash", None),
		("Cash Contribution", 100000, 50000, "Partially Paid", "Mobile Money", "TRX-FUN-001"),
		("In-Kind Contribution", 300000, 300000, "Paid", "In-Kind", None),
		("Cash Contribution", 50000, 50000, "Paid", "Cash", None),
		("Mobile Money", 150000, 150000, "Paid", "Mobile Money", "TRX-FUN-002"),
	])

	_create_contributions(graduation, graduation_guests, [
		("Cash Contribution", 100000, 100000, "Paid", "Cash", None),
		("Cash Contribution", 50000, 50000, "Paid", "Cash", None),
		("In-Kind Contribution", 75000, 75000, "Paid", "In-Kind", None),
	])
	
	# Create check-ins
	_create_checkins(wedding, wedding_guests[:6], "QR Code Scan", False)
	_create_checkins(wedding, [wedding_guests[0]], "QR Code Scan", True)  # Duplicate scan
	
	# Create committee members
	_create_committee(wedding, "Administrator", "Organizer")
	_create_committee(fundraiser, "Administrator", "Organizer")
	_create_committee(conference, "Administrator", "Organizer")
	
	frappe.db.commit()
	print("✅ Demo data seeded successfully!")
	print("   Created: 5 Events, 23 Guests, Invitations, Contributions, RSVPs, Check-Ins & Committee Members")


def _clear_existing_demo_data():
	"""Remove any previously seeded demo data by deleting documents in reverse order."""
	for doctype in ["Check-In", "RSVP", "Contribution", "Invitation", "Committee Member", "Guest", "Event"]:
		demo_names = frappe.get_all(doctype, filters={"event_name": ["like", "%Demo%"]}, pluck="name") if doctype == "Event" else []
		if not demo_names and doctype == "Event":
			# Check by organizer_name instead (demo events use specific names)
			pass
	try:
		# Clean up any existing data that matches our demo events
		demo_events = frappe.get_all("Event", filters={"organizer_name": ["in", ["John Michael", "Pastor James", "Peter Mwangi", "Grace Kimaro", "CEO Roundtable"]]}, pluck="name")
		for event_name in demo_events:
			for child_dt in ["Check-In", "RSVP", "Contribution", "Invitation", "Committee Member", "Guest"]:
				frappe.db.delete(child_dt, {"event": event_name})
			frappe.db.delete("Event", {"name": event_name})
		print("   Cleared existing demo data")
	except Exception as e:
		frappe.db.rollback()
		print(f"   Note: {e}")


def _create_event(name, event_type, status, days_from_now, time_str, venue, organizer, contact, email, max_guests):
	"""Create a demo event using raw DB insert to bypass hooks and validations."""
	import json
	now_dt = now_datetime()
	event_date = add_days(today(), days_from_now)
	
	# Generate a unique name
	from frappe.model.naming import make_autoname
	event_name = f"[Demo] {name}"
	
	# Use frappe.get_doc with all hooks disabled via flags
	ev = frappe.get_doc({"doctype": "Event"})
	ev.event_name = event_name
	ev.event_type = event_type
	ev.event_status = status
	ev.event_date = str(event_date)
	ev.event_time = time_str
	ev.venue = venue
	ev.organizer_name = organizer
	ev.organizer_contact = contact
	ev.organizer_email = email
	ev.max_guests = max_guests
	ev.flags.ignore_permissions = True
	ev.flags.ignore_validate = True
	ev.flags.ignore_mandatory = True
	ev.flags.ignore_links = True
	ev.insert()
	
	# Set creation time explicitly for ordering
	frappe.db.set_value("Event", ev.name, "creation", now_dt)
	
	print(f"   ✅ Created Event: {event_name}")
	return ev.name


def _create_guest(event, first_name, last_name, category, email, mobile, guest_type="Individual", rsvp_status=None):
	"""Create a demo guest."""
	g = frappe.new_doc("Guest")
	g.event = event
	g.first_name = first_name
	g.last_name = last_name
	g.full_name = f"{first_name} {last_name}"
	g.email = email
	g.mobile_no = mobile
	g.category = category
	g.guest_type = guest_type
	if rsvp_status:
		g.rsvp_status = rsvp_status
	g.insert(ignore_permissions=True)
	return g.name


def _create_wedding_guests(event):
	names = [
		("James", "Mwangi", "Family", "james@example.com", "+255 721 111 111"),
		("Anna", "Mbowe", "Family", "anna@example.com", "+255 721 111 112"),
		("David", "Kimaro", "Friend", "david@example.com", "+255 721 111 113"),
		("Sarah", "Lema", "Friend", "sarah@example.com", "+255 721 111 114"),
		("Michael", "John", "VIP", "michael@example.com", "+255 721 111 115"),
		("Esther", "Mushi", "Colleague", "esther@example.com", "+255 721 111 116"),
		("Paul", "Moshi", "Neighbor", "paul@example.com", "+255 721 111 117"),
		("Grace", "Nkya", "Committee", "grace@example.com", "+255 721 111 118"),
	]
	return [_create_guest(event, *n) for n in names]


def _create_fundraiser_guests(event):
	names = [
		("Joseph", "Mbilinyi", "Family", "joseph@example.com", "+255 722 222 221"),
		("Mary", "Chacha", "Friend", "mary@example.com", "+255 722 222 222"),
		("Samuel", "Ole", "VIP", "samuel@example.com", "+255 722 222 223"),
		("Ruth", "Mdoe", "Colleague", "ruth@example.com", "+255 722 222 224"),
		("Daniel", "Shao", "Neighbor", "daniel@example.com", "+255 722 222 225"),
	]
	return [_create_guest(event, *n) for n in names]


def _create_graduation_guests(event):
	names = [
		("Thomas", "Mushi", "Family", "thomas@example.com", "+255 723 333 331"),
		("Elizabeth", "Kisaka", "Family", "elizabeth@example.com", "+255 723 333 332"),
		("Patrick", "Mfinanga", "Friend", "patrick@example.com", "+255 723 333 333"),
		("Jane", "Mallya", "Friend", "jane@example.com", "+255 723 333 334"),
		("Vincent", "Massawe", "Friend", "vincent@example.com", "+255 723 333 335"),
	]
	return [_create_guest(event, *n) for n in names]


def _create_birthday_guests(event):
	names = [
		("Julia", "Lema", "Family", "julia@example.com", "+255 724 444 441"),
		("Benjamin", "Mollel", "Family", "ben@example.com", "+255 724 444 442"),
		("Monica", "Kessy", "Friend", "monica@example.com", "+255 724 444 443"),
		("Timothy", "Mngumi", "Neighbor", "tim@example.com", "+255 724 444 444"),
		("Hannah", "Mtui", "Committee", "hannah@example.com", "+255 724 444 445"),
	]
	return [_create_guest(event, *n) for n in names]


def _create_conference_guests(event):
	names = [
		("Alex", "Mrema", "VIP", "alex@example.com", "+255 725 555 551", "Organization"),
		("Diana", "Mkude", "VIP", "diana@example.com", "+255 725 555 552"),
		("Robert", "Mgana", "Colleague", "robert@example.com", "+255 725 555 553"),
		("Sophia", "Ngowi", "Colleague", "sophia@example.com", "+255 725 555 554"),
		("William", "Mpanda", "Other", "william@example.com", "+255 725 555 555"),
	]
	return [_create_guest(event, *n) for n in names]


def _create_invitations(event, guest_ids, inv_type, method):
	created = []
	for gid in guest_ids:
		guest = frappe.get_doc("Guest", gid)
		try:
			inv = frappe.new_doc("Invitation")
			inv.event = event
			inv.guest = gid
			inv.guest_name = guest.full_name
			inv.invitation_type = inv_type
			inv.delivery_method = method
			inv.status = "Ready"
			inv.insert(ignore_permissions=True)
			created.append(inv.name)
		except Exception as e:
			print(f"      ⚠️ Failed to create invitation for {guest.full_name}: {e}")
	print(f"      Created {len(created)} invitations")
	return created


def _create_rsvps(event, guest_ids, invite_ids, status, attendees):
	import random
	for i, gid in enumerate(guest_ids):
		if i >= len(invite_ids):
			break
		try:
			r = frappe.new_doc("RSVP")
			r.event = event
			r.guest = gid
			r.invitation = invite_ids[i]
			guest = frappe.get_doc("Guest", gid)
			r.guest_name = guest.full_name
			r.rsvp_status = status
			r.number_of_attendees = attendees
			r.responded_via = "WhatsApp"
			r.insert(ignore_permissions=True)
			
			# RSVP on_update hook will sync rsvp_status to guest and invitation automatically
		except Exception as e:
			print(f"      ⚠️ RSVP error: {e}")


def _create_contributions(event, guest_ids, contrib_data):
	for i, (ctype, pledged, paid, status, method, ref) in enumerate(contrib_data):
		if i >= len(guest_ids):
			break
		try:
			guest = frappe.get_doc("Guest", guest_ids[i])
			c = frappe.new_doc("Contribution")
			c.event = event
			c.guest = guest.name
			c.guest_name = guest.full_name
			c.contribution_type = ctype
			c.type = "Pledge" if paid == 0 else "Payment"
			c.pledged_amount = pledged
			c.paid_amount = paid
			c.outstanding_amount = pledged - paid
			c.payment_status = status
			if method:
				c.payment_method = method
			if ref:
				c.transaction_reference = ref
			c.currency = "TZS"
			c.insert(ignore_permissions=True)
		except Exception as e:
			print(f"      ⚠️ Contribution error: {e}")


def _create_checkins(event, guest_ids, method, is_dup):
	for gid in guest_ids:
		try:
			guest = frappe.get_doc("Guest", gid)
			ci = frappe.new_doc("Check-In")
			ci.event = event
			ci.guest = gid
			ci.guest_name = guest.full_name
			ci.invite_code = guest.invite_code
			ci.check_in_method = method
			ci.number_of_attendees = guest.number_of_attendees or 1
			ci.is_duplicate = 1 if is_dup else 0
			ci.insert(ignore_permissions=True)
			guest.db_set("checked_in", 1)
		except Exception as e:
			print(f"      ⚠️ Check-in error: {e}")


def _create_committee(event, user, role):
	try:
		cm = frappe.new_doc("Committee Member")
		cm.event = event
		cm.user = user
		cm.role = role
		cm.insert(ignore_permissions=True)
	except Exception as e:
		print(f"      ⚠️ Committee member error: {e}")


if __name__ == "__main__":
	seed_demo_data()
