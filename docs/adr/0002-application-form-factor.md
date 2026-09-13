# ADR-0002: Application form factor

- **Status:** proposed
- **Date:** 2026-09-13
- **Deciders:** Nico Schmidt
- **Supersedes:** —
- **Superseded by:** —

## Context

Before anything is built we must decide what kind of artefact this project
produces. The range is wide: at one end, a carefully written set of
instructions inside a Claude project, with no code at all; at the other, a
standalone application with a user interface, a server, persistence and its
own integration with a language model API.

The choice is not obvious, because a large part of the product value lives
in prompt and context design rather than in code. A thin solution may
deliver most of the experience. A thick solution may be needed for the parts
that a chat window structurally cannot do.

Known constraints (see `docs/vision.md`):

- Players are co-located at one table. No distributed state is required.
- The repository is public; adventure content is private and loaded at
  runtime (see ADR-0003).
- The project is deliberately an exercise in sound engineering practice.

## Decision drivers

- **What a chat window cannot do.** Hidden state the players must not see
  (monster hit points, secret doors, what the AI knows but has not told
  them), deterministic rule adjudication, reliable session persistence,
  and enforcement of the adventure's structure.
- **Context growth.** A three-hour session produces a long transcript. Some
  mechanism must decide what stays in context and what is summarised into
  durable session state.
- **Content separation.** The engine must load adventure material that is
  not in this repository, without that material leaking into places where it
  could be redistributed.
- **Testability.** Deterministic behaviour (rules, state transitions) should
  be testable without calling a model.
- **Effort.** Every layer added is a layer maintained by one person.

## Options considered

### Option A: Claude project with instructions only

The adventure and the dungeon master persona live as project instructions
and project documents. Players type into a chat window.

- Good: buildable in a day; all effort goes into prompt and content design.
- Good: model capability is used directly, with no integration surface.
- Bad: no hidden state — everything the AI knows is in a context the players
  can scroll back through.
- Bad: no deterministic rule handling; the model does the arithmetic.
- Bad: session continuity depends on the chat's own memory behaviour.
- Bad: almost nothing to engineer, test or record decisions about — which
  conflicts with a stated goal of the project.

### Option B: Local command-line application

A program that runs on one machine at the table, holding session state and
calling a model API. Text in, text out, no browser.

- Good: real code, real state, real tests, small surface.
- Good: content is loaded from a local path; nothing to secure beyond the
  filesystem.
- Bad: a terminal at a games table is a poor shared surface.
- Bad: presentation is limited when read aloud to a group.

### Option C: Full application — frontend, backend, model API

A web frontend as the shared table view, a backend holding session state,
rule adjudication and content loading, talking to a model API.

- Good: hidden state and player-visible state are genuinely separable.
- Good: deterministic logic sits in testable code, outside the model.
- Good: matches the engineering-practice goal; an honest architecture with
  real boundaries.
- Bad: the largest effort, and much of it is not the interesting part.
- Bad: risk of building infrastructure before knowing what the play
  experience actually needs.

### Option D: Thin shared client over an agent backend

A single-page frontend for the table, and a backend built on an agent
framework (e.g. the Claude Agent SDK) where the dungeon master is an agent
with tools: look up adventure state, resolve a check, update session state,
reveal information.

- Good: keeps model capability central while making state and tools explicit
  and testable.
- Good: tools are the natural place for the rules the model should not be
  improvising.
- Bad: couples the architecture to one vendor's agent abstractions.
- Bad: requires understanding the framework's boundaries before design.

## Decision

_Open. To be decided in the first architecture session._

## Open questions to resolve before deciding

1. How much hidden state does this adventure actually require? If the answer
   is "a lot", Option A is eliminated immediately.
2. Which rules must be deterministic, and which can the model adjudicate
   narratively without the players noticing or caring?
3. What is the shared surface at the table — a laptop screen, a TV, or
   someone reading aloud from a phone?
4. Must a session survive a restart, and what exactly must be remembered?
5. Is a throwaway prototype worth it to answer 1 and 2 empirically, or do we
   already know enough?

## Consequences

_To be written with the decision._
