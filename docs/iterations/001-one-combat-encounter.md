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

To be written when the goal is playable.
