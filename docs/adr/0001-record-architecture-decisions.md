# ADR-0001: Record architecture decisions

- **Status:** accepted
- **Date:** 2026-09-13
- **Deciders:** Maintainer
- **Supersedes:** —
- **Superseded by:** —

## Context

This project is developed largely with AI assistance, across sessions that
do not share memory. An assistant that cannot see why a choice was made will
either re-litigate it or quietly violate it. The same is true of a human
returning to the project after a break.

The project is also deliberately an exercise in sound software practice, so
decisions should be visible, reviewable and reversible in a controlled way.

## Decision drivers

- Continuity across sessions and across tools (Claude Code, Cowork, chat).
- The reasoning behind a choice is more valuable than the choice itself.
- Decisions must live where the code lives, not in a chat history.

## Options considered

### Option A: Architecture Decision Records in the repository

Numbered markdown files under `docs/adr/`, written before the implementing
code, immutable once accepted.

- Good: versioned, reviewable in pull requests, readable by AI assistants
  with repository access.
- Good: the history of superseded decisions survives.
- Bad: costs discipline; an unmaintained ADR set is worse than none.

### Option B: Keep decisions in chat history and issue comments

- Good: zero overhead at the moment of deciding.
- Bad: not readable by a fresh session, not diffable, not reviewable, and
  effectively lost within weeks.

## Decision

We choose **Option A**: architecture decisions are recorded as ADRs in
`docs/adr/`, using the MADR-style template in `0000-template.md`.

An ADR is required for any decision that is expensive to reverse:
technology choices, interface and data-format definitions, deployment shape,
and anything crossing a component boundary. It is written before the code
implementing it.

## Consequences

- Every architecturally significant pull request carries or references an
  ADR; the pull request template asks for it explicitly.
- `docs/architecture.md` is a derived document, updated whenever an ADR is
  accepted.
- `CLAUDE.md` instructs AI assistants to consult and to produce ADRs.
- The overhead is real and accepted: roughly one short document per
  significant decision.

## Follow-up

- ADR-0002: application form factor.
- ADR-0003: adventure content separation.
