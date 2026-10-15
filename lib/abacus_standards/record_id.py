"""abacus-record-id: the next record id for today, <project>-<YYYY-MM-DD>-<nnn>.

Retros and decision records share one sequence across every discovery
directory. Never type an id by hand.
"""
import argparse
import datetime as dt
import re
import sys

from .common import Refused, load_config, toplevel

DIRS = ("docs/retros", "docs/adr", "docs/decisions", "docs/postmortems")


def next_id(repo, day):
    project = load_config(repo)["project"]
    pat = re.compile(rf"^id:\s*{re.escape(project)}-{day}-(\d{{3}})\s*$", re.M)
    n = 0
    for d in DIRS:
        for f in (repo / d).glob("*.md") if (repo / d).exists() else []:
            for m in pat.finditer(f.read_text()):
                n = max(n, int(m.group(1)))
            fm = re.match(rf"{re.escape(project)}-{day}-(\d{{3}})", f.stem)
            if fm:
                n = max(n, int(fm.group(1)))
    return f"{project}-{day}-{n + 1:03d}"


def main(argv=None):
    p = argparse.ArgumentParser(prog="abacus-record-id", description=__doc__.split("\n")[0])
    p.add_argument("--date", default=dt.date.today().isoformat())
    a = p.parse_args(argv)
    try:
        print(next_id(toplevel(), a.date))
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
