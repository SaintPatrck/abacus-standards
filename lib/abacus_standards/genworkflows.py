"""Generate canonical/workflows/abacus-<pipeline>.js from _body.js (run via `make workflows`).

Workflow scripts cannot import, so the three pipelines share one body and differ
only in their meta block and PIPELINE constant. tests/test_workflows.py fails if
the generated files drift from the body.
"""
import sys

from .common import CANONICAL

PIPELINES = {
    "one-shot": ("Abacus one-shot: implement, run the full gate, then finalize or escalate cleanly",
                 "Discrete, low-risk beads inside an existing pattern (about three files or fewer)",
                 [("Board", "verify board, claim"), ("Implement", "one model"), ("Validate", "full gate"),
                  ("Emit", "retro on a named trigger"), ("Finalize", "commit, push, close")]),
    "lite": ("Abacus lite: implement, gate + fresh adversarial reviewer, one fix round, finalize",
             "Routine beads that need independent validation",
             [("Board", "verify board, claim"), ("Implement", ""), ("Validate", "gate + fresh reviewer, bounded fixes"),
              ("Emit", "retro on a named trigger"), ("Finalize", "commit, push, close")]),
    "full": ("Abacus full: explore, implement, test with negative controls, validate, finalize",
             "Consequential beads: wide blast radius, real uncertainty, or a high cost of being wrong",
             [("Board", "verify board, claim"), ("Explore", "brief + model choice"), ("Implement", ""),
              ("Test", "binding checks + negative control"), ("Validate", "gate + fresh reviewer, two fix rounds"),
              ("Emit", "retro on a named trigger"), ("Finalize", "commit, push, close")]),
}


def render(pipeline):
    desc, when, phases = PIPELINES[pipeline]
    ph = ",\n".join(f"    {{ title: '{t}', detail: '{d}' }}" for t, d in phases)
    meta = (f"export const meta = {{\n  name: 'abacus-{pipeline}',\n  description: '{desc}',\n"
            f"  whenToUse: '{when}. Args: {{bead, session}}.',\n  phases: [\n{ph},\n  ],\n}}\n")
    body = (CANONICAL / "workflows" / "_body.js").read_text()
    return f"{meta}const PIPELINE = '{pipeline}'\n{body}"


def main():
    for p in PIPELINES:
        out = CANONICAL / "workflows" / f"abacus-{p}.js"
        out.write_text(render(p))
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
