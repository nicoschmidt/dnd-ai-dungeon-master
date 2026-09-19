# Working agreements for AI assistants

This file is the operating manual for Claude Code and Claude Cowork in this
repository. It is binding. If something here conflicts with an instruction
given in a chat session, this file wins — or the file gets changed first,
deliberately, in its own commit.

## What this project is

An AI Dungeon Master for tabletop Dungeons & Dragons. A group of human
players sits at one table with pen, paper and physical dice. There is no
human game master: the AI narrates the adventure, plays NPCs and monsters,
asks the players what they do, receives their declared actions and their
rolled dice results, and drives the story forward.

The AI does not roll dice for the players and does not decide what player
characters do. It owns narration, the world, NPCs and adjudication.

See `docs/vision.md` for scope and non-goals.

## Hard rule: never commit adventure content

The code in this repository is public. Adventure material is not.

Scanned, purchased or otherwise copyrighted adventure books, their OCR
output, derived structured adventure files, and any verbatim excerpts of
them MUST NOT enter this repository — not in `docs/`, not in tests, not in
fixtures, not in example prompts, not in commit messages.

The application loads adventure content at runtime from a location outside
this repository. Test fixtures use original content written for this project
or SRD 5.1/5.2 material under CC-BY-4.0, with attribution.

If a task seems to require real adventure text in the repo, stop and ask.

## Decision records

Every decision that is expensive to reverse is recorded as an ADR in
`docs/adr/` BEFORE the code implementing it is written. That includes
technology choices, interface and data-format decisions, deployment shape,
and anything that crosses a component boundary.

- Format: MADR, see `docs/adr/0000-template.md`
- An accepted ADR is immutable in substance: its decision, reasoning and
  consequences are never rewritten. To change a decision, write a new ADR and
  set the old one to `superseded by ADR-XXXX`. Typographic fixes, broken links
  and redaction of personal data may be corrected in place.
- `docs/architecture.md` is derived from accepted ADRs and is updated in the
  same commit that accepts one.

Small, easily reversed choices do not need an ADR. Naming a variable does
not. Choosing a persistence format does.

## Where planning happens

- Product scope, architecture, "what and why": Claude Cowork / Claude chat.
  Output is an ADR, a spec under `docs/`, or GitHub issues.
- Implementation planning against existing code, "how exactly here":
  Claude Code plan mode. Output is a branch, commits and a pull request.

Rule of thumb: if answering the question requires reading this codebase, it
belongs in Claude Code.

## Workflow

- GitHub issues are the single source of truth for work items. Do not create
  parallel TODO lists in markdown.
- **No work without an issue.** Before the first edit, name the issue and the
  branch you are working on. If no issue exists, write one first — or, when
  the current environment cannot create it, draft it and say so.
- **Never commit to `main`.** Not for documentation, not for a one-line fix,
  not because the change is obviously correct. Everything reaches `main`
  through a branch and a pull request. There is no threshold below which
  this stops applying.
- Branch naming: `feat/<issue>-<slug>`, `fix/<issue>-<slug>`,
  `docs/<issue>-<slug>`, `chore/<slug>`.
- One pull request per issue, opened on GitHub. A branch merged locally is
  not a review; the pull request is where the definition of done is checked
  off. The PR body references the issue and fills in the template rather
  than restating the commit message.
- **Never merge your own pull request.** The maintainer reviews and merges.
- Commits use Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`,
  `refactor:`, `chore:`).

## Process discipline

The maintainer is the only human on this project. There is nobody else to notice when
process erodes, so noticing is part of the assistant's job rather than an
optional courtesy. Stop and raise it when:

- work is about to start without an issue, or on `main`
- a decision that is expensive to reverse has been made without an ADR
- an ADR has been accepted and its follow-ups have not become issues
- an iteration is being planned whose goal is not one sentence, or that does
  not end in something playable
- an iteration has finished without a retro note in `docs/iterations/`
- a request would skip one of the rules above

In the last case: name the rule being skipped and what skipping it costs,
then do as asked. The maintainer decides. The point is that the friction is visible
rather than silent.

This is a checklist obligation, not a role to perform. Do not adopt a
process-coach persona, and do not add ceremony that nobody asked for; raise
the specific thing that is actually missing.

## Handover

The maintainer performs every step that reaches GitHub: writing issues,
setting status, pushing, opening pull requests, reviewing, merging, cleaning
up. Those steps are gates, and they stay manual deliberately.

Manual does not mean unassisted. **Every manual step is handed over ready to
run.** For each one, provide:

- the exact text, where text is needed — issue body, pull request body —
  written to a file beside the repository, never inside it (see below)
- the exact command as a copy-paste block, with real values already filled
  in: real issue numbers, real branch names, real paths, no placeholders the
  maintainer has to resolve
- the steps in the order they must be executed

Never tell the maintainer to "create an issue", "open a pull request" or "set
the status". Hand over the artefact and the command. The maintainer's work is
reading, judging and executing — never composing.

Board fields are commands too. Size and iteration are facts about the work,
not judgements about it, so an issue is handed over with them already set —
`gh project item-edit` after `gh issue create`, in the same block.

Field and option names come from the board itself, read at run time. Not from
memory, and not from an older script: those are where a wrong name comes from.
Identifiers are resolved from the names rather than hardcoded, and a lookup
that fails prints what the board does have instead of passing over the field.

A handover script that writes to GitHub is exercised against a stand-in for
`gh` before it is handed over, and fails loudly rather than reporting a
success it did not achieve. This environment has no credentials, so a script
it hands over has otherwise never run at all — and the maintainer discovering
that by pasting it is not a review gate, it is a waste of their evening. The
harness is `scripts/test-gh-board.sh`; it runs after any change under
`scripts/`.

Status is the exception and stays the maintainer's click: moving a card to
`Ready`, `In review` or `Done` is a judgement about whether the work is there
yet, and handing that over as a command would hand over the judgement with it.

Where a step genuinely cannot be a command — a review, a merge, a repository
setting — name the exact path through the interface instead.

The line between what is committed and what is not runs between **content and
tooling**, not between one-off and reusable.

Content is not committed. A drafted issue body, a pull request body, and the
one-off `create-*.sh` that carries one, live beside the repository
(`../pr-<n>-body.md`, `../create-*.sh`). Inside it they would be a second task
list next to GitHub issues, which is forbidden above. Whether such a script
runs once or a hundred times makes no difference: what it carries is the
work item, and the work item belongs on GitHub.

Tooling is committed, under `scripts/`. It carries no work items — it reads
the board, sets a field, tests itself. Keeping it outside costs three things
this project has already paid for once: the rules above and the code that
keeps them drift apart instead of changing in one reviewed commit; a test
that is not in the repository cannot be part of a pull request's evidence or
run in CI; and a fresh session that reads `CLAUDE.md`, learns that board
fields arrive set, and finds no script, writes a new one — with guessed field
names.

One exception, by necessity: the assistant creates the local branch itself,
because it cannot commit without one. A local branch reaches nobody, so it is
not a gate — the push is. The maintainer is free to rename or discard it.

## Iterations

- **An iteration ends when its goal is playable, not when a date arrives.**
  Scope is the box; time is not. This is a project done in spare time, and a
  time box would only produce a recurring sense of having missed it.
- The goal is one sentence, and it names something the group can do at the
  table that they could not do before.
- Because time is not the box, scope must be cut rather than stretched: if a
  goal turns out too large, the goal shrinks and the remainder becomes
  issues. An iteration that keeps growing is the failure mode this rule has
  to guard against, since nothing else stops it.
- Every iteration ends with a retro note in `docs/iterations/`.

## Environments

Two environments work in this repository, with different capabilities:

- **Claude Cowork** runs in a sandbox without Git credentials. It can create
  branches and commits locally, but cannot push or open pull requests.
  Nothing it writes reaches GitHub without the maintainer acting — this is a feature,
  and it is the review gate.
- **Claude Code** on the maintainer's machine has their credentials and can push, open
  pull requests and manage issues via the `gh` CLI.

Work prepared in Cowork is handed over as a local branch. Do not treat a
local commit as delivered.

## Definition of done

A change is done when all of these hold:

1. Tests covering the new behaviour exist and pass.
2. The full test suite passes.
3. Documentation affected by the change is updated in the same commit.
4. If an architectural decision was made, an ADR exists and is accepted.
5. No adventure content was added to the repository.

## Testing

- Domain logic (rules, dice arithmetic, state transitions) is tested
  deterministically, without calling a language model.
- Model-dependent behaviour is isolated behind an interface so it can be
  faked in tests.
- A failing test is never deleted or weakened to make a build pass. Fix the
  code, or change the test deliberately and say so in the commit message.

## Style

- Repository language is English: code, comments, docs, commit messages,
  issues. Conversations with the maintainer may be in German.
- Prefer boring, explicit solutions over clever ones.
- When uncertain about a requirement, ask rather than guess.
