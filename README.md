# Invite — Event Management

A complete event management solution for organising guests, invitations,
contributions, and QR-based check-in for community ceremonies and special
events (weddings, funerals, harambee, graduations, church events…).

Built on **Frappe** (Python backend) with a **Vue 3 + frappe-ui + Tailwind**
SPA served at `/invite`, plus public server-rendered pages for guests.

---

## Table of contents

1. [What the system does](#what-the-system-does)
2. [Roles & who sees what](#roles--who-sees-what)
3. [Phase 0 — Installation & configuration](#phase-0--installation--configuration)
4. [Phase 1 — Events](#phase-1--events)
5. [Phase 2 — Guests](#phase-2--guests)
6. [Phase 3 — Invitations](#phase-3--invitations)
7. [Phase 4 — RSVPs](#phase-4--rsvps)
8. [Phase 5 — Check-in & the frontdesk](#phase-5--check-in--the-frontdesk)
9. [Phase 6 — After the event (reminders & thank-yous)](#phase-6--after-the-event-reminders--thank-yous)
10. [Phase 7 — Audit log & reports](#phase-7--audit-log--reports)
11. [Integrations](#integrations)
    - [WhatsApp via Meta Cloud API](#whatsapp-via-meta-cloud-api)
    - [WhatsApp via Twilio Content API](#whatsapp-via-twilio-content-api)
    - [Google Calendar](#google-calendar)
    - [Email](#email)
12. [Notifications in the app](#notifications-in-the-app)
13. [Testing runbook (quick end-to-end)](#testing-runbook-quick-end-to-end)
14. [Troubleshooting](#troubleshooting)
15. [Frontend design system](#frontend-design-system)
16. [Development](#development)

---

## What the system does

| Capability | Where |
| --- | --- |
| Create and manage events through a lifecycle (Planning → … → Completed/Cancelled) | `/invite/events` |
| Manage per-event guest lists (manual add or CSV import) | Event → **Guests** |
| Issue invitations with unique codes, QR codes and personalised PDF cards | Event → **Invitations** |
| Deliver invitations over WhatsApp (Meta or Twilio), Email, SMS or manually | Event → **Invitations** |
| Collect guest responses on a public RSVP page | `/rsvp?code=<INVITE_CODE>` |
| Scan guests in at the door (QR / code / search) from a scanner kiosk | `/invite/frontdesk` |
| Track everything in an audit log and live dashboard | Audit Log, Dashboard, Reports |
| Send reminders and thank-you messages | Scheduled tasks + Event actions |
| Sync events to Google Calendar | Event → Settings |

**Key data model (doctypes)**

| Doctype | Purpose |
| --- | --- |
| `Event` | The ceremony/gathering; stores statistics counters refreshed automatically |
| `Event Type` | Category used on cards/RSVP (Wedding, Funeral, Harambee…) |
| `Event Status` | Lifecycle status with a colour (`Planning`, `Invitations Sent`, `RSVPs Open`, `Ongoing`, `Completed`, `Cancelled`) |
| `Guest` | One record **per event per person**; holds contact, category, invite code, RSVP and check-in state |
| `Guest Category` | Family / Friend / VIP / etc. |
| `Invitation` | Guest↔event invitation; unique `invite_code`, QR payload/image, delivery status |
| `RSVP` | A response record (Accepted / Declined / Maybe) with attendee count and message |
| `Check-In` | One row per scan with duplicate detection |
| `Message Template` | Default WhatsApp/email wording used by the UI |
| `Event Settings` | Single (global) settings: currency, QR style, WhatsApp providers, Google, **frontdesk role** |
| `Invite Activity Log` | Audit trail of every meaningful action |

The frontend SPA lives in `frontend/`; server-rendered guest pages are in
`invite/www/` (`rsvp`, `invite`, `public event`). All business logic that the
UI calls is in `invite/api/*`.

---

## Roles & who sees what

Set up these **User** accounts and give them **Roles** (Frappe backend: User →
Add Role):

| Account | Suggested roles | What they get |
| --- | --- | --- |
| Organiser/Admin | `Administrator` or `System Manager` | Everything; lands on the normal Dashboard |
| Event manager | `Event Manager` (+ `Desk User`) | Full control of events, guests, invitations |
| Frontdesk scanner | `Scanner` (or any role you choose) **only** | Landed on the Frontdesk scanning page and restricted to it |
| Read-only viewer | any user | Guests/Events have read permission for role `All` |

### Frontdesk routing logic

Event Settings → **Frontdesk** tab → **Frontdesk Role** selects which role
identifies a “frontdesk operator”. After login (`/invite`):

- A user **who has that role** is sent automatically to `/invite/frontdesk`
  and the sidebar only shows Frontdesk + Audit Log.
- Everyone **else** uses the normal workspace (`/invite/dashboard`).
- If **no frontdesk role is configured**, nobody is redirected — every user
  sees the normal dashboard.

> ⚠️ Administrator note: Frappe grants `Administrator` every role in the
> system implicitly (`frappe.permissions.get_roles`). The role check
> explicitly excludes `Administrator` so an admin is never treated as a
> frontdesk-only user even if they "have" the configured role. Test scanner
> routing with the dedicated scanner account, not Administrator.

---

## Phase 0 — Installation & configuration

### Install the app

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/j0sh01/Invite.git --branch develop   # or main
bench --site YOUR_SITE install-app invite
bench --site YOUR_SITE migrate
```

Default lookup data (event types, statuses, guest categories, RSVP statuses,
message templates, Event Settings with `TZS`) is created automatically on
install.

### Configure Event Settings

Open **Event Settings** in the Frappe backend, or use the in-app
**Settings** page (`/invite/settings`) for most fields.

**General**
- `Default Currency` — used when creating events (e.g. `TZS`).
- `Default Event Type`, `Default Reminder Days Before`.

**QR code settings**
- Foreground/background colour and QR size — used when QR images are rendered.

**Frontdesk**
- `Frontdesk Role` — see [Roles & who sees what](#roles--who-sees-what).

**WhatsApp** (choose one provider — see [Integrations](#integrations)):

| Provider (dropdown value) | Required fields |
| --- | --- |
| `Official WhatsApp API` | `WhatsApp API Access Token`, `Phone Number ID`, `Business Number`, API version (`v21.0`) |
| `Twilio` | `Account SID`, `Auth Token`, `Twilio WhatsApp Number` + Content Template SIDs |

**Google Calendar** — `Client ID` + `Client Secret` (see
[Google Calendar](#google-calendar)).

### Message templates

`Message Template` records provide default wording for invitation,
confirmation, reminder and thank-you messages (with placeholders such as
`{guest_name}`, `{event_name}`, `{event_date}`, `{venue}`, `{rsvp_link}`).
They are used as copy presets by the invitation UI.

> Sending at scale uses Twilio/Meta **content templates** — see
> [Integrations](#integrations). The template body text on this doctype is
> for display/presets.

---

## Phase 1 — Events

**UI:** `Dashboard → New Event`, or `Events → New Event`.

1. Give the event a **name**, **type** (e.g. Wedding), **status**
   (starts at *Planning*), **date/time**, **venue/address**, **organiser**
   details and optional **image**, **max guests**, **description**.
2. Configuration options per event (Event → **Settings** tab):
   - `Currency`
   - `Enable Reminders` + how many days before the event
   - `QR position on card` (Left/Center/Right)
   - `Enable Public RSVP` (controls public page visibility)
   - Google Calendar sync (see [Google Calendar](#google-calendar))
3. Statistics (**Total guests / invited / RSVP’d / accepted / declined /
   checked-in**) update automatically as guests, RSVPs and check-ins change.

**Statuses move the event through its life**: Planning → Invitations Sent →
RSVPs Open → Ongoing → Completed (or Cancelled). Use the status the same way
you would a pipeline — the frontend shows a colour per status.

**Test it**
1. Create an event for a future date → appears on Dashboard + Events.
2. Edit it, upload an image → card artwork and RSVP page use it.
3. Note stats columns show zeros until you add guests.

---

## Phase 2 — Guests

**UI:** open an Event → **Guests**.

### Add one guest
Click **Add Guest** and fill in first/last name, email, mobile, category,
attendee count and optional plus-one. Guests are **per event** — the same
person attending two events is two Guest records.

Duplicate protection: an email or mobile number can only be used once per
event (an error is raised otherwise).

### Import many guests (CSV)
1. **Guests → Import → Download template** to fetch a CSV with the expected
   columns:
   `First Name *, Last Name, Email, Mobile No, Category, Number of Attendees,
   Plus One (0/1), Plus One Name`
2. Fill rows, upload the CSV in the import dialog and confirm.
3. Headers are matched loosely (e.g. `Phone` → mobile, `+1` → plus-one),
   unknown columns are ignored with a warning; per-row errors are reported
   back with row numbers.

### What a Guest record holds
- Contact, category, attendee count, plus-one name.
- **Invitation section**: status + invite code + QR, synced automatically
  from the linked `Invitation`.
- **RSVP section**: `rsvp_status`, response date, attendee count.
- **Check-in section**: `checked_in`, time and who checked them in.

**Test it**
1. Add 5 guests; CSV-import 10 more → totals increase on Event stats.
2. Try adding a duplicate email to the same event → rejected.
3. Edit a guest after sending invites — Invitation rows keep their own copy
   of the name (change shows on new sends).

---

## Phase 3 — Invitations

**UI:** open an Event → **Invitations**.

### 1. Create invitations
Select guests (or “create for all guests”) → **Create Invitations**.
One `Invitation` row is created per guest with:
- a unique `invite_code` (also written back to the Guest record),
- the QR payload URL: `/api/method/invite.api.check_in.scan_qr?code=<CODE>&event=<EVENT>`,
- status `Ready`, delivery method (default WhatsApp).

Creating an invitation for a guest who already has one for that event is
blocked (with a clear error).

### 2. Generate the QR image & invitation card
Per invitation (or bulk):
- **Generate QR** creates the PNG (`/files/qr_<CODE>.png`) and attaches it to
  the invitation and guest.
- **Generate Card** produces a personalised two-page PDF (`/files/invitation_<CODE>.pdf`):
  page 1 = event print layout with the guest-name banner, page 2 = big QR for
  scanning. Requires an **event image** — upload one first or the call fails
  with a helpful message.

### 3. Send
- **Send all** (bulk) sends every invitation in `Draft`/`Ready`; each becomes
  `Sent` (with `sent_at`) or `Failed` (error stored).
- **Resend / retry** a single failed invitation — clears the old error and
  sends again.
- If no WhatsApp provider is configured the send path is still exercised for
  Email/SMS/Manual deliveries (marked sent without an API call).

Delivery state machine: `Draft → Ready → Sent → Delivered` (or `Failed`,
`Cancelled`). WhatsApp delivery receipts are not parsed; treat `Sent` as
"dispatched", and mark `Delivered` manually if you track that.

An hourly scheduled job (`invite.tasks.process_pending_invitations`) picks up
anything left in `Ready` with a WhatsApp/SMS delivery method and sends it, so
invitations created near an event never get stuck.

**Test it**
1. Create an event → 3 guests → invitations for all 3.
2. Generate QR for one and scan it with your phone → check-in API responds.
3. Send a single invitation to your own WhatsApp number → verify arrival.
4. Break a number on purpose → row goes `Failed`; fix and retry → `Sent`.

---

## Phase 4 — RSVPs

Guests respond through two public pages (no login):

| Page | When |
| --- | --- |
| `/rsvp?code=<INVITE_CODE>` | Link embedded in every invitation/reminder; shows event details and an Accept / Maybe / Decline form with attendee count and a message box. Guests can update their answer later. |
| `/event/<EVENT_NAME>` | Public event page (frontend) with event info; uses `enable_public_rsvp` where relevant. |

Each submission creates or updates an `RSVP` record linked to the invitation
and guest (`responded_via = Web`) and the Guest record is kept in sync
(status, date, attendee count). The event statistics refresh automatically,
and every change is written to the activity log.

RSVP statuses: `Pending → Accepted / Declined / Maybe`. Guests who decline
are still listed (helpful for final counts) and are skipped by reminder jobs.

**Test it**
1. Open an invitation → copy its RSVP link (shown in the UI).
2. Open it in a private/incognito window, respond *Accepted* with 3
   attendees → Event stats increment.
3. Respond again as *Maybe* → the same RSVP is updated, not duplicated.
4. Confirm the guest’s row in **Guests** shows the new status.

---

## Phase 5 — Check-in & the frontdesk

**UI:** `/invite/frontdesk` (auto-landing for the frontdesk role).

1. **Pick the event** — only guests of the selected event can check in.
2. Scan the guest’s QR (camera), type the invite code manually, or **search**
   by name/code/phone and tap the guest.
3. The guest is recorded as a `Check-In` (`is_duplicate` = 0) and their Guest
   record flips to `checked_in` with timestamp + operator. Event “checked in”
   counters rise instantly. Re-scanning the same guest marks a **duplicate**
   scan instead of a second check-in (visible in the log).

The kiosk shows live totals (guests / checked in / accepted / rate) so the
door team knows exactly where the event stands.

**Permissions:** the frontdesk API reads events and guests with
`ignore_permissions=True`, so the scanner account does not need full system
roles — it just needs the configured **frontdesk role** (and the role list
logic from Phase 0).

**Test it**
1. Log in as the scanner account → you land on `/invite/frontdesk`.
2. Select an event; search a guest by name → check them in.
3. Scan their QR again → duplicate warning, counters unchanged.
4. Confirm the check-in appears in the event’s Recent check-ins & audit log.

---

## Phase 6 — After the event (reminders & thank-yous)

### Reminders (automatic)
Daily job `invite.tasks.send_reminder_notifications`: for events **3 days
away** with reminders enabled, guests still on `Pending` get a
Notification Log reminder.

### Reminders (WhatsApp/email, from the UI)
Event actions can send reminders on demand through the configured channel
(`invite.api.card.send_reminders`): every guest with a contact gets the
reminder; an attached invitation-card PDF goes along via WhatsApp media/email.

### Thank-you messages
- Automatic daily job for **Completed** events: checked-in guests receive a
  thank-you Notification Log.
- Manual send per event to checked-in guests (email and/or WhatsApp), with
  the event image attached.

### Manual notification logs
Every dispatched WhatsApp/email in these flows is also written to Frappe’s
`Notification Log` (visible under the bell in the app) so there is an
in-app audit even when the SMS gateway is not configured yet.

**Test it**
1. Create an event 3 days in the future with reminders on, add a guest with
   `Pending` → run `bench --site <site> execute invite.tasks.send_reminder_notifications`
   → Notification Log row appears for the guest.
2. Mark an event Completed with past date + a checked-in guest → run the
   thank-you task → log row appears.

---

## Phase 7 — Audit log & reports

**Audit log** (`/invite/audit-log`, and per-event **Audit Log** tab) lists
guest create/edit/delete, invitation created/sent/failed, QR & card
generation, RSVP submissions, check-ins (with duplicate flag), reminders and
thank-yous — filterable by category and action.

**Dashboard / Reports** give the running numbers:
- Dashboard: total events, upcoming, guests, checked in + recent events.
- Event → **Reports**: guest breakdown by category, RSVP breakdown with
  attendee sums, check-in totals/duplicates, and a full guest export.

---

## Integrations

### WhatsApp via Meta Cloud API

Used when `WhatsApp Provider = Official WhatsApp API`.

**Setup (one time, in Event Settings / Settings page):**
1. Create/use a WhatsApp Business account and a Meta developer app
   (https://developers.facebook.com/docs/whatsapp/cloud-api/get-started).
2. Fill: **Access Token**, **Phone Number ID**, **Business Number**
   (`+2557…`), API version `v21.0`.
3. (Optional) Set a **message template** in Meta; the app currently sends
   plain text and media (no template-SID flow for Meta — that flow exists for
   Twilio).

**Behaviour**
- Text: `invite.api.whatsapp.send_text_message` posts to
  `graph.facebook.com/<version>/<phone_number_id>/messages`; recipient
  numbers are sent without `+`.
- Media (invitation PDF/image): file is resolved via Frappe file manager
  (public `/files/...` or full URL), uploaded to Meta to get a `media_id`,
  then sent as an image/document with a caption. MIME type is guessed from
  the extension.
- Errors are logged to `Error Log` under “WhatsApp Integration”.

**Test it**
- Settings page → choose Official WhatsApp API, fill token/phone number ID,
  Save, then send a test invite to your own number from Invitations.
- Expect: delivery on the phone, invitation row → `Sent`, no Error Log entry.

### WhatsApp via Twilio Content API

Used when `WhatsApp Provider = Twilio`.

**Setup:**
1. Twilio account → verify your WhatsApp number (or sandbox) and build
   **content templates** in Twilio’s Content Template Builder
   (https://www.twilio.com/console/sms/content-templates).
2. Fill Account SID, Auth Token, Twilio WhatsApp number.
3. Paste each template SID into the matching field:

| Field | Used for |
| --- | --- |
| `Twilio Template Invitation` | event invitations |
| `Twilio Template RSVP Confirm` | RSVP confirmations |
| `Twilio Template RSVP Reminder` | RSVP reminders |
| `Twilio Template Event Reminder` | event reminders |
| `Twilio Template Event Update` | event updates |
| `Twilio Template QR Check-in` | QR/check-in messages |
| `Twilio Template Thank You` | thank-you messages |

**Behaviour**
- Sending a WhatsApp invitation builds numbered variables from the
  invitation/event: `{{1}}` guest name, `{{2}}` event name, `{{3}}` date,
  `{{4}}` time, `{{5}}` venue, `{{6}}` RSVP link.
- If a matching template SID is **not configured**, the code falls back to a
  plain-text message (still via Twilio) so invitations never silently fail.
- The Settings page has **Test Connection** and **Fetch My Templates**
  (lists your content templates and shows diagnostics) plus **Send Test**.

**Test it**
- Fill SID/token, click Test Connection → green diagnostics; Send Test to
  your WhatsApp; send one invitation → guest receives it.

### Google Calendar

Connects the organiser’s Google account so events can be pushed to their
primary calendar.

1. Google Cloud console → enable **Google Calendar API**, create **OAuth 2.0
   Web application** credentials.
2. Set redirect URI to
   `https://YOUR-SITE/api/method/invite.api.google_calendar.oauth_callback`.
3. Store **Client ID** and **Client Secret** in Event Settings.
4. In Event → Settings, **Connect calendar** (authorises the current user),
   then **Sync to calendar**; the resulting Google event id is stored on the
   Event (`google_calendar_event_id`) and the event appears with a Google
   Calendar link.
5. **Disconnect** clears the stored tokens.

Endpoints: `get_auth_url`, `oauth_callback`, `get_connection_status`,
`sync_event_to_calendar`, `disconnect_calendar`.

> Tokens are stored on the User record. If your site’s User doctype has not
> been customised with those fields, connect first via the documented flow
> after migrating — errors will surface in Error Log under “Google Calendar”.

### Email

Reminders and thank-yous support an email channel. Frappe’s outbound mail
must be configured for the site (System Settings → Email, or an Email
Account marked default outbound). Emails are queued via `EmailQueue`; the
event image or invitation card can be attached.

---

## Notifications in the app

- Bell (top of the sidebar) lists `Notification Log` entries for the current
  user (new event activity, reminders, thank-yous) with an unread counter.
- Changes are pushed over websockets (realtime `refetch_resource`) so open
  pages refresh without a manual reload.

---

## Testing runbook (quick end-to-end)

The fastest full pass that exercises every module:

1. **Config:** set WhatsApp provider + credentials (your choice of Meta or
   Twilio), frontdesk role = `Scanner`, add a scanner user.
2. **Event:** create *Wedding* event 30 days out, add image + venue.
3. **Guests:** import 10 via CSV, add 2 manually; confirm dedupe.
4. **Invitations:** create for all 12; generate QR on one; generate the PDF
   card for one (needs event image); bulk-send via WhatsApp (mock provider if
   not configured yet → rows become `Sent`).
5. **RSVP:** open `/rsvp?code=<CODE>`; respond Accepted w/ 2 attendees;
   re-open and change to Maybe.
6. **Frontdesk:** login as scanner → auto-land; pick event; search & check in
   two guests; re-scan one → duplicate.
7. **Audit:** verify log rows for guest create, invitation sent, RSVP,
   check-in, duplicate.
8. **Reports:** open event reports; check RSVP breakdown & guest export.
9. **Post-event:** move event to Completed with past date; run the two
   scheduled tasks and confirm Notification Log rows.
10. **Integrations:** Twilio Test Connection + Fetch Templates + Send Test;
    or Meta — send an invite to your own phone and confirm media card
    delivery; Google — connect & sync one event.

---

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| I’m always sent to `/invite/frontdesk` | The account is `Administrator` and a frontdesk role is configured. Administrator implicitly holds every role in Frappe; the check excludes Administrator by design. Log in as the real user to verify their routing. |
| Frontdesk scanner can’t see events | Ensure Event Settings → Frontdesk Role is set and the account has that role. The APIs read with `ignore_permissions`, so no extra system roles are required. |
| WhatsApp sends fail with no error | Provider not enabled: confirm dropdown value (`Official WhatsApp API` / `Twilio`) and that all credential fields are filled; watch Error Log entries named “WhatsApp Integration” / “Twilio Integration”. |
| Meta media (card PDF) fails | Files must be publicly readable (`/files/...`). QR images and invitation cards are stored under public files. |
| Twilio template fallback used instead of template | The template SID field is blank or the SID doesn’t match a content template; the app falls back to plain text deliberately. |
| Invitation stuck on `Ready` | Either send it manually or wait for the hourly `process_pending_invitations` job (only processes WhatsApp/SMS delivery methods). |
| Event stats look stale | Counters refresh on document events (guest/invitation/RSVP/check-in saves). After a bulk import/migration, edit+save the Event once to recompute. |
| QR scan opens a login page | The guest scanner page requires a logged-in frontdesk user; scanning is handled inside `/invite/frontdesk`, not a guest-facing endpoint. |
| Public RSVP shows “Invitation Not Found” | Wrong/expired code — verify against the Invitation record (invite codes are unique). |
| Reminders/thank-yous don’t send WhatsApp | Scheduled jobs create Notification Log entries; WhatsApp/email dispatch is driven from Event actions. Configure mail for email channel. |

---

## Frontend design system

The UI follows a **warm editorial** system so it doesn’t look like a default
template:

- **Palette:** parchment canvas (`#F4EDE1`), paper cards (`#FFFDF8`),
  espresso ink surfaces, terracotta accent (aliased as `blue` in Tailwind so
  frappe-ui primaries inherit it). Warm gray scale replaces the default cool
  gray; frappe-ui tokens are overridden in `src/index.css` (`:root` and
  `[data-theme=dark]`).
- **Type:** serif display headings (`font-display`, Iowan/Palatino/Georgia
  stack) + small-caps eyebrow labels (`eyebrow`).
- **Primitives** in `frontend/src/components/ui/`: `PageHeader`, `StatCard`,
  `StatusBadge` (dot pills), `EmptyState`, `QuickAction`. Shared helpers:
  `utils/format.js` (dates/times/plurals) and `utils/status.js` (single
  status→colour mapping for every page).
- **Shell:** espresso sidebar (desktop + mobile drawer) with grouped
  navigation that adapts to the frontdesk role; warm canvas content area.
- Pages are being migrated to this system in reviewable batches (shell +
  Dashboard + Events + Event detail first; Guests, Invitations, Check-In,
  Frontdesk, Audit, Reports, Settings and public pages to follow).

When restyling a page: reuse the UI primitives above, prefer
`font-display`/`eyebrow`/`card` classes, and never hard-code a new status
colour — add it to `utils/status.js` instead.

---

## Development

```bash
# backend (frappe site "mchango" in this bench)
bench --site mchango migrate
bench --site mchango console

# frontend (from frontend/)
cd frontend
npm install          # first time
npm run dev          # vite dev server proxying to frappe (HMR)
npm run build        # production build → writes app public assets and
                     # rewrites invite/www/invite.html entry points

# scheduled tasks (or use bench schedule for cron-equivalent)
bench --site mchango execute invite.tasks.send_reminder_notifications
bench --site mchango execute invite.tasks.send_thank_you_messages
bench --site mchango execute invite.tasks.process_pending_invitations
```

### Linting

Pre-commit runs ruff (Python) and eslint/prettier (frontend):

```bash
cd apps/invite && pre-commit install
```

### License
MIT
