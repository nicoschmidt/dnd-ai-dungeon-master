# Iterations

One file per iteration, named `NNN-<short-goal>.md`.

Each iteration states:

- **Goal** — one sentence. What can we do at the end that we could not do
  before?
- **Scope** — the issues pulled in, by number.
- **Out of scope** — what was deliberately deferred, and why.
- **Result** — filled in at the end: what shipped, what did not, what we
  learned.

Iterations are tracked on the GitHub Project board via the `Iteration`
field. This folder holds the narrative that the board cannot.

## Planned iterations and the MVP

An iteration is a unit of work: one goal, and it ends when that goal is
playable. The **MVP** is not a unit of work. It is a milestone — the first
iteration after which the group would choose to spend an evening playing with
the application — and it is reached by iterations like any other result.

The iterations up to the MVP are planned ahead, so that each one knows what the
next needs from it. A planned iteration gets its file here before it starts,
with **Goal** and **Out of scope** filled in; **Scope** grows as issues are
written for it and is settled when the iteration starts; **Result** is written
at the end, as always. The goals of planned iterations change when an earlier
one teaches something — that is what planning ahead is for, not a failure of
it.

| Iteration | Goal in brief | Proves |
| --- | --- | --- |
| [001](001-one-combat-encounter.md) | One combat encounter against one opponent | The engine: streaming, the tool boundary, deterministic rules, the party panel |
| [002](002-one-scene-from-our-adventure.md) | One scene from the maintainer's own adventure | The content boundary: schema, loader, hidden and revealed information |
| [003](003-one-evening-of-play.md) | One evening through one chapter | **The MVP.** Ingest from the scan, scene progression, resuming after a restart |

Status is not kept here. Which issues are open, in progress or done is on the
board and in each iteration's epic; this table says only what each iteration
is for.
