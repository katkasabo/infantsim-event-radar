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
a tag outside this list will throw when a card renders, because the label lookup
in `index.html` has no fallback.

### Participation route shape

```jsonc
{
  "mode": "abstract",               // attend | abstract | pitch | exhibit
  "label": "Submit an abstract",
  "deadline": "2026-11-02",         // ISO or null
  "deadlineLabel": "12 Aug to 2 Nov 2026",  // the human string
  "status": "open",                 // open | closed | unannounced | rolling
  "note": ""
}
```

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
3. Check the confirmed events for changed dates or venues.
4. Update `events.json`, and add a dated entry to the `changelog` array at the
   top of that file. The site's "What changed" tab renders it.
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
