app_name = "invite"
app_title = "Invite"
app_publisher = "Joshua Michael"
app_description = "A complete event management solution for organizing guests, invitations, contributions, and QR-based check-in for community ceremonies and special events."
app_email = "joshuajmichael255@gmail.com"
app_license = "mit"

# Apps
add_to_apps_screen = [
	{
		"name": "invite",
		"logo": "/assets/invite/images/logo.svg",
		"title": "Invite",
		"route": "/invite",
		"has_permission": "invite.api.check_app_permission",
	}
]

# Home Pages
website_route_rules = [
	{"from_route": "/invite/<path:app_path>", "to_route": "invite"},
]

# Installation
before_install = "invite.install.before_install"
after_install = "invite.install.after_install"

# Uninstallation
before_uninstall = "invite.uninstall.before_uninstall"

# DocType Class
override_doctype_class = {}

# Document Events
doc_events = {
	"Invitation": {
		"before_insert": ["invite.api.invitation.before_insert"],
		"after_insert": ["invite.api.invitation.after_insert"],
	},
	"RSVP": {
		"on_update": ["invite.api.rsvp.on_update"],
	},
	"Contribution": {
		"validate": ["invite.api.contribution.validate"],
	},
}

# Scheduled Tasks
scheduler_events = {
	"daily": [
		"invite.tasks.send_reminder_notifications",
		"invite.tasks.send_thank_you_messages",
		"invite.tasks.send_contribution_reminders",
	],
	"hourly": [
		"invite.tasks.process_pending_invitations",
	],
}

# Testing
# before_tests = "invite.install.before_tests"

# User Data Protection
# user_data_fields = []

# Authentication and authorization
# auth_hooks = []

after_migrate = []

standard_dropdown_items = [
	{
		"name1": "app_selector",
		"label": "Apps",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "toggle_theme",
		"label": "Toggle theme",
		"type": "Route",
		"icon": "moon",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "settings",
		"label": "Settings",
		"type": "Route",
		"icon": "settings",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "about",
		"label": "About",
		"type": "Route",
		"icon": "info",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "separator",
		"label": "",
		"type": "Separator",
		"is_standard": 1,
	},
	{
		"name1": "logout",
		"label": "Log out",
		"type": "Route",
		"icon": "log-out",
		"route": "#",
		"is_standard": 1,
	},
]
