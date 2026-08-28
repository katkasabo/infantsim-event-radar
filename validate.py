#!/usr/bin/env python3
"""
Pre-commit check for events.json.

Exists because status was being inferred from a missing date rather than read off
the page, which shipped four wrong statuses in one sitting. The rule that broke:
"I could not find a date" is not the same fact as "the organiser has not published
one". Machine checks, not good intentions.

    python3 validate.py            # structural checks, fast
    python3 validate.py --links    # also HTTP-check every source URL, slow

Exit code 1 if any ERROR. Warnings never fail the build.
"""
import json, sys, datetime, collections, re

TODAY = datetime.date.today()
STALE_DAYS = 45
MODES = {"present", "pitch", "attend", "exhibit"}
TAGS = {"pediatric", "surgery", "simulation", "startup", "industry"}
STATUSES = {"open", "closed", "unannounced", "rolling"}
BASES = {"published", "prior-year", "approx", "free", "unknown"}
ABSENT = {"none", "n/a"}

errors, warns = [], []
def E(where, msg): errors.append(f"{where}: {msg}")
def W(where, msg): warns.append(f"{where}: {msg}")

def iso(s):
    try: return datetime.date.fromisoformat(s)
    except Exception: return None

TYPES = {"conference", "competition", "accelerator"}

d = json.load(open("events.json"))
events = d["events"]

ids = [e["id"] for e in events]
for dup, n in collections.Counter(ids).items():
    if n > 1: E(dup, f"duplicate event id, {n} copies")

by_source = collections.defaultdict(list)

for e in events:
    eid = e["id"]

    if e.get("type") not in TYPES:
        E(eid, f"type is {e.get('type')!r}, expected one of {sorted(TYPES)}")

    for t in e.get("tags", []):
        if t not in TAGS: E(eid, f"unknown tag {t!r}")

    start = iso(e.get("start") or "")
    if start and start < TODAY and e.get("confirmed"):
        W(eid, f"start date {e['start']} is in the past. Roll it to the next edition.")

    v = iso(e.get("verified") or "")
    if not v:
        W(eid, "never verified")
    elif (TODAY - v).days > STALE_DAYS:
        W(eid, f"last verified {e['verified']}, {(TODAY - v).days} days ago")

    labels = collections.Counter(p["label"] for p in e.get("participate", []))
    for lab, n in labels.items():
        if n > 1: E(eid, f"two routes share the label {lab!r}, so cells cannot be told apart")

    for p in e.get("participate", []):
        w = f"{eid} / {p.get('label','?')}"

        if p.get("mode") not in MODES: E(w, f"unknown mode {p.get('mode')!r}")
        st = p.get("status")
        if st not in STATUSES: E(w, f"unknown status {st!r}")

        dl = iso(p.get("deadline") or "")
        if p.get("deadline") and not dl:
            E(w, f"deadline {p['deadline']!r} is not an ISO date")

        # --- the checks that would have caught the four bad statuses ---
        if dl and dl < TODAY and st != "closed":
            E(w, f"deadline {p['deadline']} has passed but status is {st!r}. "
                 f"A passed date means closed.")
        if st == "unannounced" and dl:
            E(w, f"status is 'unannounced' but a deadline of {p['deadline']} is set. "
                 f"Pick one: either the organiser published a date or they did not.")
        if st == "open" and not dl:
            E(w, "status is 'open' with no deadline. Use 'rolling' for an open-ended "
                 "window, or 'unannounced' if no date has been published.")
        if st == "unannounced" and not p.get("checked"):
            W(w, "claims 'unannounced' with no `checked` note saying what the page showed. "
                 "This is the state that gets guessed. Read the page and record it.")

        c = p.get("cost")
        if not isinstance(c, dict):
            E(w, "no cost object")
        else:
            if not c.get("amount"): E(w, "cost has no amount")
            if c.get("basis") not in BASES: E(w, f"unknown cost basis {c.get('basis')!r}")
            if not c.get("source"): E(w, "cost has no source link")
            if c.get("basis") == "unknown" and not re.search(r"not published|coming soon|prospectus|"
                    r"on request|quote|contact|available soon|not posted|not retriev|behind",
                    (c.get("detail") or ""), re.I):
                W(w, "cost basis is 'unknown' but the detail does not say where the figure "
                     "lives or who to ask")

        # An unpriced route must still prove the route EXISTS. Otherwise a generic
        # "contact us" invitation renders identically to a real offer with a hidden
        # price, which is how a fabricated sponsorship row shipped once.
        if (c or {}).get("basis") == "unknown" and not p.get("checked"):
            E(w, "cost is 'unknown' with no `checked` note. Evidence that this route "
                 "actually exists, or delete it and set absent[mode]='none'.")

        # Katka's rule: for every event x column, either it is n/a, or we say under
        # what conditions, for how much, and when and how to register.
        for f, why in [("conditions", "who can take this route and on what terms"),
                       ("how", "when and how to register or apply"),
                       ("gain", "what you get out of it")]:
            if not p.get(f):
                E(w, f"no `{f}`: every route must say {why}")

        if p.get("mode") == "pitch" and not p.get("prize"):
            W(w, "pitch route with no prize recorded. Cost alone is half the decision: "
                 "say what can be won, even if that is 'Not published'.")
        pz = p.get("prize")
        if pz and not pz.get("source"):
            E(w, "prize has no source link")

        if not (p.get("url") or (c or {}).get("source")):
            E(w, "no link at all, so the table cell cannot link out")

        src = p.get("url") or (c or {}).get("source")
        if src: by_source[src].append((w, st))

    absent = e.get("absent", {})
    for m, kind in absent.items():
        if m not in MODES: E(eid, f"absent names unknown mode {m!r}")
        if kind not in ABSENT: E(eid, f"absent[{m}] is {kind!r}, expected one of {sorted(ABSENT)}")
        if kind == "none" and not e.get("absentSrc", {}).get(m):
            W(eid, f"absent[{m}] claims 'none found' with no absentSrc link proving what was checked")
        if kind == "none" and not e.get("absentWhy", {}).get(m):
            W(eid, f"absent[{m}] claims 'none found' with no absentWhy explaining what was looked for")
        if any(p["mode"] == m for p in e.get("participate", [])):
            E(eid, f"absent[{m}] is set but a {m} route also exists")

    for m in MODES:
        if not any(p["mode"] == m for p in e.get("participate", [])) and m not in absent:
            W(eid, f"{m}: no route and no absent entry, so the cell reads 'Not checked'")

# routes sharing a source page should not disagree about whether that page is open
for src, rows in by_source.items():
    sts = {s for _, s in rows}
    if len(rows) > 1 and {"unannounced"} & sts and ({"open", "closed", "rolling"} & sts):
        W("cross-check", f"one source, disagreeing statuses {sorted(sts)} -> {src}\n"
                         + "\n".join(f"      {w} = {s}" for w, s in rows))

if "--links" in sys.argv:
    import urllib.request, urllib.error, ssl
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    urls = sorted({u for e in events for p in e["participate"]
                   for u in [p.get("url"), p.get("cost", {}).get("source")] if u}
                  | {l["url"] for e in events for l in e.get("links", [])}
                  | {u for e in events for u in e.get("absentSrc", {}).values()})
    print(f"checking {len(urls)} unique links...", file=sys.stderr)
    for u in urls:
        try:
            req = urllib.request.Request(u, method="GET",
                    headers={"User-Agent": "Mozilla/5.0 (radar link check)"})
            with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
                if r.status >= 400: E("link", f"HTTP {r.status} -> {u}")
        except urllib.error.HTTPError as err:
            (E if err.code in (404, 410) else W)("link", f"HTTP {err.code} -> {u}")
        except Exception as err:
            W("link", f"{type(err).__name__}: {err} -> {u}")

routes = sum(len(e["participate"]) for e in events)
print(f"{len(events)} events, {routes} routes")
if warns:
    print(f"\n{len(warns)} warning(s):")
    for x in warns: print("  -", x)
if errors:
    print(f"\n{len(errors)} ERROR(s):")
    for x in errors: print("  !", x)
    sys.exit(1)
print("\nno errors")
