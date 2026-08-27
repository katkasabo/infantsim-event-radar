# InfantSim Event Radar

A rolling 12-month view of pediatric, surgical, simulation and medtech-startup
events, and every deadline attached to each one. Built for Katka Sabo's US
commercialisation work with InfantSim, a Slovak neonatal MIS surgical simulator.

The site is one static page plus one data file. No build step, no framework, no
dependencies. It is published with GitHub Pages.

## Files

| File | Role | Commit? |
|---|---|---|
| `index.html` | The whole site. Fetches `events.json` on load. | yes |
| `events.json` | **Master data.** 29 events, 55 participation routes. | yes |
| `robots.txt` | Keeps the page out of search results. | yes |
| `CLAUDE.md` | This file. | yes |
| `notes.json` | **Private.** Katka's internal read on each event. | **never** |
| `infantsim-event-radar-internal.html` | Derived offline snapshot with the private notes baked in. | **never** |
| `build-internal.py` | Regenerates the snapshot above. | yes |

`notes.json` and the internal snapshot are in `.gitignore`. The repo is public.
Anything committed here is world-readable, so keep Katka's commercial judgement,
named contacts and outreach status out of it. The public page carries only what
the event organisers themselves publish.

## How the data works

`events.json` is the single source of truth. There is no spreadsheet: a Google
Sheet was the master until 26 Aug 2026 and was deprecated because it could not be
written to programmatically, so it drifted from the site.

To change the site, edit `events.json` and commit. The page fetches it with
`cache: "no-store"` and a cache-busting query param, so a refresh is enough. Do
not hand-edit the data inside `index.html`; the page holds `const EMBEDDED = null;`
and that marker must stay exactly as it is or `build-internal.py` will fail.

### Event shape

```jsonc
{
  "id": "apsa-2027",              // stable slug, also the notes.json key
  "name": "APSA 2027, 58th annual meeting",
  "org": "American Pediatric Surgical Association",
  "dateLabel": "12 to 15 May 2027", // human string shown on the card
  "start": "2027-05-12",            // ISO, drives timeline placement and sort
  "end": "2027-05-15",              // optional
  "confirmed": true,                // false renders a "not confirmed" flag
  "where": "Manchester Grand Hyatt San Diego, San Diego, CA",
  "country": "USA",
  "region": "North America",        // feeds the Where filter
  "tags": ["pediatric", "surgery", "simulation"],
  "priority": true,                 // renders a PRIORITY marker
  "summary": "...",
  "audience": "...",
  "participate": [ /* see below */ ],
  "links": [{ "label": "apsapedsurg.org", "url": "https://..." }],
  "tracker": "",                    // always empty in the public file
  "verified": "2026-08-26"          // when the source was last checked
}
```

Valid `tags`: `pediatric`, `surgery`, `simulation`, `startup`, `industry`. Adding
a tag outside this list will throw when a row renders, because the label lookup
in `index.html` has no fallback.

`absent` and `absentSrc` say, per mode, why there is no route. `absent[mode]` is
`"none"` (checked, this event does not offer it, and `absentSrc[mode]` links to
what was checked) or `"n/a"` (an application or prize, so the mode cannot apply).
A mode missing from `absent` renders as "Not checked", which is the backlog.

### Participation route shape

```jsonc
{
  "mode": "present",                // present | pitch | attend | exhibit | teach
  "label": "Submit an abstract",
  "deadline": "2026-11-02",         // ISO or null
  "deadlineLabel": "12 Aug to 2 Nov 2026",  // the human string
  "status": "open",                 // open | closed | unannounced | rolling
  "note": "",
  "url": "https://...",             // where to read more. Falls back to cost.source
  "rail": false,                    // optional. false keeps it out of "Closing next"
  "cost": {
    "amount": "EUR 847",            // what it actually costs, in full
    "detail": "Full registration incl VAT; EUR 700 excl. Nurse or student 303.",
    "basis": "published",           // published | prior-year | approx | free | unknown
    "source": "https://..."         // the link behind the figure
  }
}
```

The five modes: **present** is actively presenting, an abstract, talk or poster.
**pitch** is a startup-specific competition. **attend** is going as a regular
attendee. **exhibit** is a paid on-site presence, a booth or sponsorship.
**teach** is running a hands-on course or workshop.

`cost.amount` is the *total* cost of taking that route, not one component of it.
MEDICA is the worked example: the pitch slot is not sold on its own, so the
pitch route costs EUR 3,500, the booth plus the stage upgrade, not EUR 550.

Set `rail: false` on anything that is logistics rather than a way to take part,
such as a hotel block. It stays on the page and stays out of "Closing next".

### Reading status off a page, not guessing it

Four statuses shipped wrong in one sitting because `unannounced` was used as a
dumping ground for "I could not find a date". These are three different facts and
must not be collapsed:

| Status | Means | Test |
|---|---|---|
| `open` | A published window is running. **Requires a `deadline`.** | You can name the closing date |
| `closed` | The window has passed, **or the outcome is already public** | Date passed, or the cohort, finalists or programme are named |
| `unannounced` | The organiser has published nothing for this edition | You looked and the page says nothing |
| `rolling` | Genuinely open-ended, no closing date exists | Page says "applications open" with no date |

Two traps, both of which bit:

- **A named cohort means closed.** If the page lists who got in, the round is
  over, whatever the application page still says.
- **Page copy lies, dates do not.** AdvaMed's Call for Sessions page reads
  "Call for Sessions is open" while naming a window that closed in February.
  Believe the date, flag the page.

Every route with `status: "unannounced"` needs a `checked` field: one line saying
what the page actually showed and when. If you cannot write that line, you did not
read the page. `checked` renders in the expanded row, so it is visible to Katka.

### Before committing

```bash
python3 validate.py            # structural checks
python3 validate.py --links    # also HTTP-check every source URL
```

Errors block the commit. It catches a passed deadline that is not marked closed,
`unannounced` with a date set, `open` with no date, a missing cost or source, two
routes in one event sharing a label (which makes table cells indistinguishable),
and dead links. Warnings are the backlog, chiefly "Not checked" cells and
`unannounced` routes with no `checked` note.

### The fit score

Computed in the browser in `index.html` from `events.json`, never stored, so it
re-scores itself when the data changes. Weights live in one object, `W`, near the
top of the script; changing the model is a one-line edit.

An event scores as its single strongest route, on the grounds that one good way in
is enough to justify showing up. The breakdown renders in the expanded row so the
number is auditable and arguable.

It deliberately blends **topical fit** with **how actionable the route is today**.
An unannounced congress scores low because there is nothing to act on yet, not
because the audience is wrong. ESPNIC and jENS are the worked examples: both are
strong neonatal audiences and both score below their clinical relevance while their
dates and fees stay unpublished. Say that out loud rather than tuning the weights
until the answer looks nicer.

`closed` costs -6, but a closed route that records an `expect` window claws +5 back,
because a deadline we missed and can predict is worth more than one we cannot.

### A route must be evidenced, not inferred

An unpriced route and a route that does not exist look identical on the page, so
the difference has to live in the data. Every route whose `cost.basis` is
`unknown` must carry a `checked` note evidencing that **the route itself exists** —
an exhibitor prospectus, a named sponsorship contact, an exhibitor count, a
registration link. "This kind of congress usually has an exhibition" is not
evidence, and the validator now rejects it.

Where there is no published offer, delete the route and set `absent[mode]` to
`"none"`, with `absentSrc[mode]` linking to what was checked and `absentWhy[mode]`
saying what was looked for. Both render on the page.

This rule exists because a "Sponsor the day" row was invented for the Helsinki
event off a generic "Become a sponsor" invitation, and then displayed as a live
rolling route with a hidden price. An open-ended invitation to email someone is
not a route you can plan or budget against.

### Prices hide one click inside the booking flow

If registration is open, the rates are usually reachable, just not on the page you
land on. Two worked examples, both of which read "not published" until someone
pushed further: MEDICA's visitor prices sit in the Messe Duesseldorf shop
(EUR 50 a day, EUR 150 for the four days), and the Helsinki event's free ticket is
only visible in the Eventbrite listing's structured data. Fetching the marketing
page and recording "not published" is the failure mode. Open the shop.

### One row per named call

If an organiser publishes several distinct calls, each gets its own route with its
own name and window. PAS is the worked example: it publishes six, and collapsing
them into "Submit an abstract" and "Call for sessions" produced two table cells
that both read "Not published" with different countdowns and no way to tell them
apart. Route labels are what the table cell shows, so they must be specific enough
to identify the route on their own, and unique within an event.

Status is recomputed in the browser against today's date. A route with a
`deadline` in the past renders as closed regardless of the stored `status`, and
one within 30 days renders in the urgent colour. So `status` only really matters
for `unannounced` and `rolling`, which have no date to compute from. Set
`deadline: null` for those.

## The weekly job

Katka gets a digest each Sunday. Around 32 participation routes have no published
date yet; the point of the job is to catch them turning into real dates. The
routine, in order:

1. Search Gmail for subject `RADAR: new event` in the last 7 days. Those come
   from the intake form on the site's "Add an event" tab. Research each and add it.
2. Re-check every route with `"status": "unannounced"` against its source link.
   Then clear down some "Not checked" cells: pick a few and either add a route
   with a sourced cost, or set `absent[mode]` to `"none"` with an `absentSrc`.
3. Check the confirmed events for changed dates or venues.
4. Update `events.json`, and add a dated entry to the `changelog` array at the
   top of that file. The site's "What changed" tab renders it.
4b. Run `python3 validate.py --links` and fix every error before committing.
5. Commit and push. The live site updates immediately.
6. Email the digest to katka@sabotageworks.com, subject
   `InfantSim event radar, week of [date]`, sections in this order: closing in
   the next 30 days with days remaining, newly published deadlines, new events
   added, changed dates or venues, count still waiting on an announcement. If
   nothing changed, say so in one line and send anyway.

Report what the sources say. No ranking, no recommendations. Private judgement
goes in `notes.json`, not in the public data.

## Known open items

- **jENS 2027** abstract deadline is 31 Mar 2027. An earlier record said 2026;
  that was wrong and is fixed. Do not reintroduce it.
- **APSA 2027** call for abstracts has not been posted. The 2026 guide appeared
  in August of the preceding year, so it is overdue. Check weekly.
- **MedTech Innovator** has moved its deadline earlier two years running:
  15 Jan 2025, then 1 Dec 2025. The 2027 window is unannounced.
- **SIM Expo 2026** has two conflicting submission deadlines on record,
  17 Apr and 13 Jul. Unresolved.

## Writing conventions

Katka's, and they apply to the page copy, the digest and commit messages:

- No em dashes. Use en dashes or colons.
- Lead with the short version, then the supporting detail.
- Bullets over paragraphs for anything structured.
- Every external figure needs a working link behind it. If the link cannot be
  found, rebuild the claim on something defensible rather than asserting it.
- Her name is always **Katka Sabo**. Slovak rendered without diacritics.

## Rebuilding the internal snapshot

```bash
python3 build-internal.py
```

Reads `index.html`, `events.json` and `notes.json`; writes
`infantsim-event-radar-internal.html`. Python 3 standard library only. Run it
after any change to `events.json` or `notes.json` that Katka needs offline.
