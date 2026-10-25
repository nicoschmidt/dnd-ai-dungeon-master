# Working agreements for AI assistants

This file is binding. If something here conflicts with an instruction given
in a session, this file wins — or the file gets changed first, deliberately,
in its own pull request.

The way of working is [ai-dev-process](https://github.com/nicoschmidt/ai-dev-process),
at the version in `.ai-dev-process.lock`. Its rules are in
`.claude/rules/process/`, which Claude Code loads automatically. **A chat
session reads every file there before it starts work.** Those files are
managed upstream and never edited here; this file holds what is particular to
this project.

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
fixtures, not in example prompts, not in commit messages, not in issues.

The application loads adventure content at runtime from a location outside
this repository. Test fixtures use original content written for this project
or SRD 5.1/5.2 material under CC-BY-4.0, with attribution. See
[ADR-0003](docs/adr/0003-adventure-content-separation.md).

If a task seems to require real adventure text in the repo, stop and ask.

Mechanism: `scripts/check-no-adventure-content.sh` runs in CI and fails on
adventure content paths, binaries, images and fixtures without a
`PROVENANCE.md`; see `scripts/README.md`. It is a heuristic and cannot tell
whether a paragraph was copied out of a book — this rule can.

If an adventure file has landed anyway: remove it before the commit is
pushed. If it was already pushed, the history has to be rewritten — a
genuinely bad afternoon, which is why the rule exists.

## Process parameters

| Parameter | Value |
| --- | --- |
| Iteration done criterion | playable at the table: the group can do it with the application, without anyone explaining the tool |
| Iteration box | scope — this is a spare-time project, and a time box would only produce a recurring sense of having missed it |
| Repository language | English |
| Conversation language | German |
| Branch types | feat, fix, docs, chore |
| Board fields (facts) | Size (the board may call it Größe), Iteration |
| Process repository | nicoschmidt/ai-dev-process |

## Definition of done additions

- No adventure content was added to the repository.

## Testing in this project

The rules in `.claude/rules/process/quality.md` apply as written. Here, the
deterministic domain logic is the rules core — dice arithmetic, attacks,
damage, state transitions — and the dependency behind an interface is the
language model: no test calls one.

## Process deviations

None.

## Commands

```bash
# once per clone
git config core.hooksPath .githooks

# backend
pip install -e '.[dev]' && pytest

# client
cd client && npm ci && npm test && npm run lint && npm run build

# scripts and repository guards, as CI runs them
bash scripts/process/check-kit.sh
bash scripts/check-no-adventure-content.sh
```

CI requires one check, `CI passed`. A new job in `.github/workflows/ci.yml`
joins that job's `needs` list; `tests/test_ci_workflow.py` fails when it does
not.
