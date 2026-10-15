"""abacus-authorize: the operator grants ONE human-only act to an agent session (operator-run only).

  abacus-authorize decision [--repo PATH] [--ttl MIN] [--note TEXT]   one write/delete of a decision record
  abacus-authorize browser  [--repo PATH] [--ttl MIN] [--note TEXT]   one browser/computer-use act
  abacus-authorize list                                               open and recently used grants

A grant is consumed by the human-only guard on the first matching tool call, then it is spent.
Agents cannot run this command (the guard refuses it) and cannot write the grant files (they live
under ~/.abacus, behind the repo fence and role policy).
"""
import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

ACTIONS = ("decision", "browser")


def grants_dir():
    d = Path(os.environ.get("ABACUS_HOME", Path.home() / ".abacus")).expanduser() / "state" / "authorizations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def main(argv=None):
    p = argparse.ArgumentParser(prog="abacus-authorize", description=__doc__.split("\n")[0])
    p.add_argument("action", choices=ACTIONS + ("list",))
    p.add_argument("--repo", default=".", help="repository (or role directory) the grant applies to")
    p.add_argument("--ttl", type=int, default=30, help="minutes until the grant expires unused (default 30)")
    p.add_argument("--note", default="", help="what you are authorizing, for the record")
    a = p.parse_args(argv)
    d = grants_dir()
    if a.action == "list":
        for f in sorted(d.glob("*.json*")):
            g = json.loads(f.read_text())
            state = "used" if f.name.endswith(".used") else ("expired" if g["expires"] < time.time() else "open")
            print(f"{g['id']}  {state:<7} {g['action']:<8} {g['repo']}  {g.get('note', '')}")
        return 0
    gid = secrets.token_hex(4)
    grant = {"id": gid, "action": a.action, "repo": os.path.realpath(a.repo), "created": time.time(),
             "expires": time.time() + a.ttl * 60, "note": a.note}
    (d / f"{gid}.json").write_text(json.dumps(grant, indent=2))
    print(f"granted {a.action} once in {grant['repo']} (id {gid}, expires in {a.ttl} min)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
