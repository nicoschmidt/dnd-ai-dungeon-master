# 003 — One evening of play

Planned. Not started. **This iteration is the MVP.**

## Goal

The group plays a whole evening through one chapter of the maintainer's own
adventure: several scenes in sequence, the AI keeps track of where the party is
and what it knows, and when the evening ends the session resumes where it
stopped.

## What it proves

That the application replaces a human game master for an evening — the
measure in [docs/vision.md](../vision.md): the group plays for hours without
anyone explaining the tool, and wants to play again.

## Scope so far

Epic: #37.

Known needs, to become issues when 002 has taught what they look like:

- the ingest pipeline producing a whole chapter from the scan
- moving between scenes, and tracking adventure progress as durable state
- persistence and resuming — a decision record first; whether the journal from
  [ADR-0006](../adr/0006-game-master-view-and-session-journal.md) is its basis
  is part of that decision
- context growth over a long session: what stays in the model's context and
  what is summarised into state ([ADR-0002](../adr/0002-application-form-factor.md))

## Out of scope

- A second adventure.
- Everything that [docs/vision.md](../vision.md) lists as out of scope.

## Result

To be written when the goal is playable.
