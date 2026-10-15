# Abacus conventions (v1)

What the orchestrator relies on in every adopted repository. The doctor's check name is in brackets.

## Lifecycle of a unit of work
- Work is a **bead** on the repository's own board [board]. Its description begins `FILED AGAINST: <sha>`. Its
  acceptance criteria live in the acceptance field, one observable per bullet.
- A bead labeled `draft` was proposed by the planner and isn't approved yet: it never runs (`abacus-board brief`
  refuses it). Approval, by the operator's own words, gives it a pipeline label and lifts `draft`.
- Every open non-epic bead carries exactly one **pipeline label** set by the board's owner [labels]:
  `pipeline:one-shot` (discrete, about three files or fewer, inside an existing pattern), `pipeline:lite` (routine;
  independent validation), `pipeline:full` (consequential: blast radius, uncertainty, cost of being wrong),
  `pipeline:manual` (a person drives the session), `pipeline:operator` (changes to the agent's own controls).
- Work runs through the matching **Dynamic Workflow** [workflows]: board → (explore) → implement → (test) → validate →
  emit → finalize, with a read-only probe after every stage.
- Only **abacus-finalize** commits, pushes and closes [close-out-door], and only when every criterion is `met` with
  evidence or `moved` to a valid measurement bead. Order: commit → check trailers → push (gate) → close.
- **Cross-repository waits**: a bead that needs another repository's work says so in its description as
  `WAITS-ON <repo>:<bead> (<what must be true there>)`, with an `external:<repo>:<capability>` edge. Acceptance
  criteria check only their own repository; the orchestrator checks the other side before dispatch, enforces the wait
  with `dispatch add --requires-verified`, and records the verified commit on the dispatch.

## Safety boundaries
- Guards are byte-identical to canonical and wired [guards]. Repos earn `bypassPermissions` only when this check is
  ADOPTED.
- Secrets: the `secrets` guard and the `redact.py` PostToolUse hook are wired for every tool [guards]. Repos add
  their own names and files with `secret_env_names` and `secret_paths` in `.abacus/config.json`.
- Commit gate (`fast_check`) and push gate (`gate`, under the heavy lock) [gate].
- Run artifacts live in `.abacus-runs/`, which is gitignored [runs-ignored].
- One CLAUDE.md paragraph covers *instruction edits*, what is *delegated*, and what *changes authority* [instruction].
  CLAUDE.md stays short [instruction-size].

## Records
- **Emit** [emit, obligation]: retros, decisions and postmortems carry the ten-key header and pass
  `abacus-validate-records`. Ids come from `abacus-record-id`.
- **Consult** [consult, obligation]: the `abacus-memory` MCP server is registered and the corpus has rows. CLAUDE.md
  tells sessions to consult before settling an approach [memory-block].
- **Judgments**: JUDGEMENT / STANDING / OUTCOME rows, append-only on the bead, checked by `abacus-judgment check`.
  A row for a logbook ruling ends with `ruling: #<id>`.

## Declining a convention
Write `docs/adr/<id>.md` with `deviates:<check>` in its frontmatter tags; the title is the reason. The convention
then reads DEVIATING. Obligations cannot be declined.
