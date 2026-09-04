# Copyright (c) 2024, Joshua Michael and contributors
# MIT License. See license.txt

import datetime

import frappe
from frappe.utils import get_url

no_cache = 1


def get_context(context):
    """Build context for the public RSVP page."""
    frappe.db.commit()

    # Handle POST → submit RSVP
    if frappe.request and frappe.request.method == "POST":
        return _handle_rsvp_submission(context)

    # Handle GET → show form
    return _show_rsvp_form(context)


def _show_rsvp_form(context):
    """Show the RSVP form for a given invite code."""
    invite_code = frappe.local.form_dict.get("code", "").strip()

    if not invite_code:
        context.invalid = True
        context.error_message = "No invitation code provided. Please check your invitation link."
        return context

    invitation = _get_invitation(invite_code)
    if not invitation:
        context.invalid = True
        context.error_message = "Invalid invitation code. This invitation could not be found."
        return context

    guest = frappe.get_doc("Guest", invitation.guest)
    event = frappe.get_doc("Event", invitation.event)

    context.invalid = False
    context.submitted = False
    context.invitation = invitation
    context.guest = guest
    context.event = event
    context.invite_code = invite_code
    context.event_image = get_url(event.image) if event.image else ""
    context.event_date = event.event_date.strftime("%d %B %Y") if event.event_date else ""
    context.event_time = _format_time_12h(event.event_time)
    context.guest_name = guest.full_name or guest.first_name or "Guest"
    context.current_rsvp = guest.rsvp_status or ""
    context.current_attendees = guest.number_of_attendees or 1
    context.site_url = get_url()

    return context


def _handle_rsvp_submission(context):
    """Process RSVP form submission."""
    form = frappe.local.form_dict
    invite_code = form.get("code", "").strip()
    status = form.get("status", "Accepted").strip()
    attendees = int(form.get("attendees", 1))
    message = form.get("message", "").strip()

    if not invite_code:
        context.invalid = True
        context.error_message = "No invitation code provided."
        return context

    if status not in ("Accepted", "Declined", "Maybe"):
        context.invalid = True
        context.error_message = "Please select a valid RSVP status."
        return _show_rsvp_form(context)

    invitation = _get_invitation(invite_code)
    if not invitation:
        context.invalid = True
        context.error_message = "Invalid invitation code."
        return context

    try:
        # Create or update RSVP document directly
        existing = frappe.db.get_value("RSVP", {
            "invitation": invitation.name, "guest": invitation.guest
        }, "name")

        if existing:
            rsvp = frappe.get_doc("RSVP", existing)
        else:
            rsvp = frappe.new_doc("RSVP")

        rsvp.event = invitation.event
        rsvp.guest = invitation.guest
        rsvp.invitation = invitation.name
        rsvp.rsvp_status = status
        rsvp.number_of_attendees = attendees
        rsvp.message = message
        rsvp.responded_via = "Web"

        if existing:
            rsvp.save(ignore_permissions=True)
        else:
            rsvp.insert(ignore_permissions=True)

        frappe.db.commit()

        # Reload guest to get updated status
        guest = frappe.get_doc("Guest", invitation.guest)

        context.submitted = True
        context.submitted_status = status
        context.submitted_attendees = attendees
        context.invite_code = invite_code
        context.event = frappe.get_doc("Event", invitation.event)
        context.guest = guest
        context.guest_name = guest.full_name or guest.first_name or "Guest"
        context.invalid = False

    except Exception as e:
        frappe.db.rollback()
        context.error = str(e)
        return _show_rsvp_form(context)

    return context


def _format_time_12h(value):
    """Format a Frappe Time value as 12-hour clock time for display.

    Frappe hands Time fields back as ``datetime.timedelta`` (seconds since
    midnight) on some versions and ``datetime.time`` on others, so the value
    can't be formatted with ``strftime`` directly.
    """
    if not value:
        return ""

    if isinstance(value, datetime.timedelta):
        hours, minutes = divmod(int(value.total_seconds()) // 60, 60)
        hours %= 24
    elif isinstance(value, datetime.time):
        hours, minutes = value.hour, value.minute
    elif isinstance(value, str):
        parts = value.strip().split(":")
        if not parts or not parts[0].isdigit():
            return ""
        hours = int(parts[0]) % 24
        minutes = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    else:
        return str(value)

    suffix = "AM" if hours < 12 else "PM"
    hours12 = hours % 12 or 12
    return f"{hours12}:{minutes:02d} {suffix}"


def _get_invitation(invite_code):
    """Look up invitation by invite code."""
    try:
        invitations = frappe.get_all(
            "Invitation",
            filters={"invite_code": invite_code},
            fields=["name", "guest", "event"],
            limit=1,
        )
        if invitations:
            return frappe.get_doc("Invitation", invitations[0].name)
    except Exception:
        pass
    return None
