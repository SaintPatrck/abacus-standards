# abacus-standards

The standards repository for [Abacus](https://github.com/dasien/abacus). It **defines** the conventions every participating repository
adopts, **packages** their shared implementation, **inspects** adoption with `abacus-doctor`, and **rolls out**
updates with `abacus-adopt`. It owns no application code.

## Contents
```
canonical/
  hooks/guards.py, _shell.py     PreToolUse guards (one process): repo-fence, foreign-bd, destructive-git,
                                 stage-writes, database-url, operator-only, secrets, human-only
                                 (+ role-policy and role-commands, wired only for the agent roles; foreign-bd
                                 also holds the planner to drafts it may label only with an operator ruling)
  hooks/_secrets.py, redact.py   secret names/files/token shapes; PostToolUse output redaction (fails closed)
  workflows/_body.js             shared Dynamic Workflow body -> abacus-{one-shot,lite,full}.js (make workflows)
  skills/                        abacus-worker (worker contract), abacus-run-bead, bead-file, bead-close,
                                 judgments, adversarial-review, retro
  githooks/pre-commit, pre-push  fast check / full gate under the heavy lock
  templates/                     settings.hooks.json, CLAUDE.abacus.md
conventions/README.md            the canonical description of each convention
bin/                             abacus-doctor, abacus-adopt, abacus-finalize, abacus-board (brief, check,
                                 find: search every fleet board), abacus-judgment,
                                 abacus-authorize (operator-only one-time grants),
                                 abacus-record-id, abacus-validate-records
tests/                           negative controls for every guard, doctor/adopt/finalize, workflow sync + emit table
```

## Changing a convention
1. Edit the canonical file (for workflows, edit `_body.js` and run `make workflows`).
2. Add or adjust a negative control: a test that proves the check can fail. Run `make test`.
3. Roll it out to canaries with `abacus-adopt`, check `abacus-doctor`, then roll out to the rest.
4. Extending a closed vocabulary (record enums, pipeline labels) needs a decision record in `docs/adr/`.
