#!/usr/bin/env python3
"""
Rebuild the internal snapshot of the InfantSim event radar.

The public site is index.html + events.json. The internal snapshot is the same
page with the data and the private notes baked in, so it opens offline with a
double click and can be emailed to Petra.

Usage:  python3 build-internal.py
Output: infantsim-event-radar-internal.html  (gitignored, never commit)
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).parent
MARKER = "const EMBEDDED = null;"

def main():
    for f in ("index.html", "events.json", "notes.json"):
        if not (HERE / f).exists():
            sys.exit(f"Missing {f}. Expected it next to this script.")

    page  = (HERE / "index.html").read_text()
    data  = json.loads((HERE / "events.json").read_text())
    raw   = json.loads((HERE / "notes.json").read_text())
    notes = raw["notes"]
    decs  = raw.get("decisions", {})

    if MARKER not in page:
        sys.exit("index.html no longer contains the data marker. Check the loader in the page script.")

    for e in data["events"]:
        e["tracker"] = notes.get(e["id"], "")
        # The private overlay carries the full Yes/Maybe/No read. The public
        # events.json carries only the shortlist, because a complete decision
        # list is commercial judgement and the repo is world-readable.
        if e["id"] in decs:
            e["decision"] = decs[e["id"]]

    out = page.replace(MARKER, "const EMBEDDED = " + json.dumps(data, ensure_ascii=False) + ";")
    dest = HERE / "infantsim-event-radar-internal.html"
    dest.write_text(out)

    merged = sum(1 for e in data["events"] if e["tracker"])
    dm = sum(1 for e in data["events"] if e.get("decision"))
    print(f"Wrote {dest.name}: {len(data['events'])} events, {merged} private notes, "
          f"{dm} decisions merged.")

if __name__ == "__main__":
    main()
