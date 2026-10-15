"""abacus-judgment: the judgment loop's row grammar, checker, and review queue.

Rows are appended to a bead's notes (never edited):

  JUDGEMENT <YYYY-MM-DD>: question: ... | options: ... | recommended: ... | confidence: ... |
            review: <checkable thing> by <YYYY-MM-DD> | ruled: "<operator's words>" | agreed: yes|no|partial
            [| ruling: #<logbook ruling id>]
  STANDING <YYYY-MM-DD>: words: "..." | scope: ... | source: ... | review: <checkable thing> by <YYYY-MM-DD>
            [| ruling: #<logbook ruling id>]
  OUTCOME <YYYY-MM-DD>: ruling: <YYYY-MM-DD> #<n> | outcome: held|failed|unclear | words: "<evidence quoted>" |
            delegated: true|false | lesson: <one line or none>
  SUPERSEDED <YYYY-MM-DD>: <why>      (directly under a bad row; the corrected row follows)

  check "<row>"        print OK with the horizon and evidence source it will use, or refuse
  due [--today D]      rulings whose review horizon has passed with no OUTCOME (read-only)
  status               reviews due, outcomes by held/failed/unclear
"""
import argparse
import datetime as dt
import json
import re
import sys

from .common import Refused, bd_json, toplevel

DATE = r"\d{4}-\d{2}-\d{2}"
FIELDS = {
    "JUDGEMENT": ("question", "options", "recommended", "confidence", "review", "ruled", "agreed"),
    "STANDING": ("words", "scope", "source", "review"),
    "OUTCOME": ("ruling", "outcome", "words", "delegated", "lesson"),
}
TAG = re.compile(r"^\[from [^\]]+\]\s*")  # notes on a foreign board carry a provenance tag
BEAD_ID = re.compile(r"\b[a-z][a-z0-9-]*-[a-z0-9]*\d[a-z0-9]*(?:\.\d+)*\b")


def parse_row(row):
    row = TAG.sub("", row.strip())
    if "\n" in row:
        raise Refused("a row is one line; a newline inside a field is not allowed")
    m = re.match(rf"^(JUDGEMENT|STANDING|OUTCOME) ({DATE}): (.*)$", row.strip())
    if not m:
        raise Refused("row must start with JUDGEMENT|STANDING|OUTCOME <YYYY-MM-DD>: ")
    kind, date, rest = m.groups()
    parts = [p.strip() for p in rest.split(" | ")]
    want = FIELDS[kind]
    ruling_id = None
    if kind in ("JUDGEMENT", "STANDING") and len(parts) == len(want) + 1:
        # optional last field: the logbook ruling id, so a relayed `RULING <bead> (ruling <id>)` matches its row
        m_id = re.fullmatch(r"ruling: #(\d+)", parts[-1])
        if not m_id:
            raise Refused(f"an extra last field must be 'ruling: #<logbook ruling id>'; got {parts[-1][:40]!r}")
        ruling_id = int(m_id.group(1))
        parts = parts[:-1]
    if len(parts) != len(want):
        raise Refused(f"{kind} needs {len(want)} fields in order ({', '.join(want)}); got {len(parts)} "
                      f"(a '|' inside a field is not allowed)")
    fields = {}
    for part, key in zip(parts, want):
        if not part.startswith(f"{key}: "):
            raise Refused(f"expected field '{key}: ...' in position {want.index(key) + 1}, got {part[:40]!r}")
        fields[key] = part[len(key) + 2:]
    if ruling_id is not None:
        fields["ruling_id"] = ruling_id
    if kind == "JUDGEMENT" and fields["agreed"] not in ("yes", "no", "partial"):
        raise Refused("agreed must be yes, no or partial")
    if kind == "JUDGEMENT" and not re.fullmatch(r'".*"', fields["ruled"]):
        raise Refused('ruled must quote the operator\'s words: ruled: "<verbatim>"')
    if kind == "OUTCOME":
        if fields["outcome"] not in ("held", "failed", "unclear"):
            raise Refused("outcome must be held, failed or unclear")
        if fields["outcome"] != "unclear" and not fields["words"].strip('" '):
            raise Refused("held/failed needs quoted evidence; with no readable evidence the outcome is unclear")
        if fields["delegated"] not in ("true", "false"):
            raise Refused("delegated must be true or false")
        return kind, date, fields, None, None
    rm = re.match(rf"^(.*\S)\s+by\s+({DATE})$", fields["review"])
    if not rm:
        raise Refused("review must be '<checkable thing> by <YYYY-MM-DD>' (check and its date first)")
    horizon = rm.group(2)
    ids = BEAD_ID.findall(rm.group(1))
    evidence = ids[0] if ids else rm.group(1)
    return kind, date, fields, horizon, evidence


def rows_on_board(repo):
    items = bd_json(["list", "--all", "-n", "0"], repo) or []
    for it in items:
        notes = it.get("notes") or ""
        lines = notes.splitlines()
        lines = [TAG.sub("", ln) for ln in lines]
        for i, line in enumerate(lines):
            if line.startswith(("JUDGEMENT", "STANDING", "OUTCOME")):
                superseded = i + 1 < len(lines) and lines[i + 1].startswith("SUPERSEDED")
                yield it.get("id"), line, superseded


def due(repo, today):
    rulings, outcomes = [], set()
    for bead, line, superseded in rows_on_board(repo):
        if superseded:
            continue
        try:
            kind, date, f, horizon, evidence = parse_row(line)
        except Refused:
            continue
        if kind == "OUTCOME":
            outcomes.add((bead, f["ruling"].split()[0]))
        else:
            rulings.append({"bead": bead, "kind": kind, "date": date, "horizon": horizon, "evidence": evidence,
                            "row": line})
    return [r for r in rulings if r["horizon"] <= today and (r["bead"], r["date"]) not in outcomes]


def main(argv=None):
    p = argparse.ArgumentParser(prog="abacus-judgment", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("row")
    d = sub.add_parser("due"); d.add_argument("--today", default=dt.date.today().isoformat())
    s = sub.add_parser("status"); s.add_argument("--today", default=dt.date.today().isoformat())
    a = p.parse_args(argv)
    try:
        if a.cmd == "check":
            kind, date, f, horizon, evidence = parse_row(a.row)
            print(f"OK {kind} {date}" + (f" | horizon {horizon} | evidence {evidence}" if horizon else ""))
            return 0
        repo = toplevel()
        if a.cmd == "due":
            print(json.dumps(due(repo, a.today), indent=2))
        else:
            counts = {"held": 0, "failed": 0, "unclear": 0}
            for _, line, sup in rows_on_board(repo):
                if line.startswith("OUTCOME") and not sup:
                    try:
                        counts[parse_row(line)[2]["outcome"]] += 1
                    except Refused:
                        pass
            print(json.dumps({"reviews_due": len(due(repo, a.today)), "outcomes": counts}, indent=2))
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
