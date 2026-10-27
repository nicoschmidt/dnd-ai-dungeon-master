# 001 — One combat encounter

## Goal

The group plays a combat encounter against a single opponent at the table: the
AI narrates and plays the opponent, the players roll their own dice and report
the results, the code resolves hits and damage deterministically, and the
shared screen shows the state of the party.

## Why this slice

It is the smallest thing that exercises all three commitments of
[ADR-0002](../adr/0002-application-form-factor.md) for real: the web client
exists, combat is deterministic, and durable state changes only through tools.
It needs no adventure, so it proves the engine without waiting for the content
boundary.

## Scope

Epic: #6.

Decisions and specifications, before the code that depends on them:

- #20 — the game master view and the session journal
  ([ADR-0006](../adr/0006-game-master-view-and-session-journal.md))
- #26 — this plan
- #27 — subscription or API key
  ([ADR-0007](../adr/0007-model-credentials.md))
- #28 — the combat encounter ([docs/domain/combat.md](../domain/combat.md))

Foundation and guards:

- #22 — project skeleton: one process serving backend and client
- #24 — CI check: no web framework or Agent SDK below the API layer
- #16 — the handover script tests in CI
- #5 — CI check: no adventure content in the repository; 001 adds the first
  fixture, so the check is needed now rather than in 002

The game:

- #23 — the event contract and the dungeon master's initial tool surface
- #29 — deterministic combat in the rules core
- #30 — entering the party, and the status panel
- #31 — the opponent: an SRD stat block through the adventure port
- #49 — the encounter and opponent tools wired to the rules core; split off #29,
  which builds the rules but not the opponent state they need
- #32 — running the agent on the subscription or on an API key

Seeing what happened:

- #33 — the session journal
- #34 — the game master view

## Out of scope

- Adventure content of any kind. The opponent and the premise of the fight are
  SRD and original material; the adventure arrives in 002.
- Persistence across a restart.
- Speech input and output, map or grid, character import (#19).
- More than one opponent, and everything else listed at the end of
  [docs/domain/combat.md](../domain/combat.md).
- OpenTelemetry beyond configuration: the SDK's export stays switched off unless
  a latency question needs it.

## If it grows

This iteration is larger than the one first scoped in #6: the game master view,
the journal and the credential switch joined it on 2026-09-26. If it stops
converging, cut in this order, and move what is cut to 002:

1. The game master view shrinks to the roll records and tool calls; the plan,
   cost display and credential switch wait.
2. The game master view goes entirely; the journal file stays, and is read
   directly.

The journal itself is not a cut candidate: without it, a wrong result in a fight
cannot be traced to the model, the code or the narration.

## Result

The goal was reached. The group played the encounter at the table three times,
from the premise to the end, without anyone explaining the tool. Whether every
number was right was judged by plausibility rather than checked against a
record — which is what the journal is for.

Shipped:

- the event contract, the table's stream and declared actions (#23)
- deterministic combat in the rules core (#29), wired to the tools (#49, split
  off #29 once it was clear the rules needed opponent state)
- entering the party, and the status panel (#30)
- the SRD Ogre through the adventure port (#31)
- the dungeon master on the subscription or on an API key (#32)
- the skeleton and the CI guards (#22, #24, #16, #5)
- `docs/runtime.md` (#56), and the move to ai-dev-process (#58, #61)

Not shipped, moved to 002: the session journal (#33) and the game master view
(#34). The cut order above planned the view as the first cut and the journal as
none. Play settled it differently: the goal was playable without either, and an
iteration ends when its goal is playable. Both move to
[002](002-one-scene-from-our-adventure.md), where the view is needed for the
adventure's hidden information anyway, and the journal comes first.

What play showed beyond the goal:

- After `end_encounter` the dungeon master narrates on. The specification did
  not say what follows the end; it now does, in
  [docs/domain/combat.md](../domain/combat.md#5-end). The tools keep it honest:
  those that touch the opponent refuse once the encounter has ended.
- The screen got in the way: the party's state sat above the narration and
  scrolled out of sight, the interface was English at a German-speaking table,
  and the party was typed in again every evening. That is iteration
  [001a](001a-the-table-screen.md), epic #68.

## Process learnings

Inputs: no issue was labelled `process` during 001 — the label arrived with
ai-dev-process on 2026-10-25. None of the merged pull requests from #38 to #54
carries a review comment; their commit messages recorded what changed on the
way. Cut: #33 and #34, above. Each learning below that holds for other projects
too is an issue in the process repository.

- [generic] Five ideas from play were noted as drafts on the board, where no
  session that reads issues finds them and the retro does not see them. They
  became issues by hand — nicoschmidt/ai-dev-process#4
- [generic] A handover script run twice creates every issue twice: #49 and #50
  were created eleven seconds apart, and #60 duplicated #61. The script for 001a
  already reuses an issue whose title exists — nicoschmidt/ai-dev-process#5
- [generic] "What the reviews had to correct" is empty by construction when one
  maintainer reviews by reading; the useful trace was in commit messages ("goes
  beyond #24 as written", "changes deliberately") — nicoschmidt/ai-dev-process#6
- [generic] The goal was played several times before anyone closed the
  iteration, because the open issues looked like unfinished work rather than
  scope to move — nicoschmidt/ai-dev-process#7
- [project] On the board, #20, #26 and #27 carried the iteration `Backlog`
  although this file names them in 001's scope. Corrected on the board; nothing
  in `CLAUDE.md` follows from it.
