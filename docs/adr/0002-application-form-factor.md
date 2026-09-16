# ADR-0002: Application form factor

- **Status:** accepted
- **Date:** 2026-09-16
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
- **Incremental delivery.** Each iteration must end in something playable.
  The architecture must allow responsibility to move from the model into
  code over time, without a rewrite.
- **Effort.** Every layer added is a layer maintained by one person.

## Options considered

### Option A: Claude project with instructions only

The adventure and the dungeon master persona live as project instructions
and project documents. Players type into a chat window.

- Good: buildable in a day; all effort goes into prompt and content design.
- Bad: no hidden state — everything the AI knows sits in a context the
  players can scroll back through. Asymmetric information is the core of the
  game master's role, and this option cannot provide it.
- Bad: no deterministic rule handling; the model does the arithmetic.
- Bad: almost nothing to engineer, test or record decisions about, which
  conflicts with a stated goal of the project.

### Option B: Local command-line application

A program that runs on one machine at the table, holding session state and
calling a model API. Text in, text out, no browser.

- Good: real code, real state, real tests, small surface.
- Bad: a terminal is a poor shared surface at a games table, and it forecloses
  the party status panel and the map visualisation we already know we want.

### Option C: Full application — frontend, backend, model API

A web frontend as the shared table view, a backend holding session state,
rule adjudication and content loading, talking to a model API.

- Good: hidden state and player-visible state are genuinely separable.
- Good: deterministic logic sits in testable code, outside the model.
- Bad: the largest effort, and the risk of building infrastructure before
  knowing what the play experience needs.

### Option D: Thin shared client over an agent backend

A frontend for the table, and a backend built on an agent framework where
the dungeon master is an agent with tools: read adventure state, resolve a
check, update session state, reveal information.

- Good: keeps model capability central while making state and tools explicit
  and testable.
- Good: tools are the natural place for rules the model should not improvise.
- Bad: couples the architecture to one vendor's agent abstractions.

## Decision

We build **a web application with a Python backend in which the dungeon
master is an agent with explicit tools** — Options C and D combined. The
Claude Agent SDK provides the agent loop; Python is the implementation
language for the backend and the rules core, chosen because it is the
language Nico knows best and because the rules core is ordinary,
test-friendly domain logic.

Three commitments follow from this, and they are the substance of the
decision:

**1. The web client exists from the first iteration.** Even when it only
renders a text log and an input field, it is the shared surface at the
table. It is the thing that later grows a party status panel and a map, and
retrofitting a UI onto a command-line application would mean rebuilding the
transport and the state model.

**2. Rules move from the model into code over iterations, not all at once.**
Early iterations may let the agent adjudicate narratively where writing the
rule would cost more than it is worth. Later iterations replace that
judgement with deterministic Python. Combat is the first area to become
deterministic, because it is the most arithmetic and the least forgiving of
inconsistency.

**3. Durable state changes only through tools.** The agent narrates, decides
and asks; it does not mutate state by describing a mutation. Anything that
must survive a restart or must be shown on the status panel — hit points,
conditions, position, adventure progress, what the party knows — changes
only via a tool call against state the backend owns.

Commitment 3 is what makes commitment 2 possible. If a tool's contract is
stable, its implementation can start as "ask the model" and later become
"compute it", and nothing above the tool boundary has to change. A tool
whose contract is designed around how the model happens to behave today
would destroy that property, so tool interfaces are designed from the
domain, not from the model.

Narrative context that does not need to survive a restart — tone, recent
phrasing, the texture of the scene — stays in the model's context and is not
modelled as state. Drawing that line is a recurring design decision, not a
one-off.

## Consequences

What becomes easy:

- Hidden state is real: the backend decides what the client renders, so
  monster hit points and unrevealed adventure content never reach the table.
- The rules core is a pure Python module, testable without a model.
- The status panel and, later, the map are views over state that already
  exists, not new subsystems.
- Sessions can be persisted and resumed, because durable state is explicit.

What becomes hard, and what we accept:

- This is the largest of the four options. Iteration 1 must be scoped
  aggressively or it will not end in something playable.
- Coupling to the Claude Agent SDK is accepted. The mitigation is that the
  rules core and state model do not import it; only the orchestration layer
  does.
- Latency is now ours to manage: a model call between a player speaking and
  the table hearing an answer is felt at the table in a way it is not in a
  chat window.
- The temptation will be to let the agent handle "just this one thing"
  informally. The definition of done and the tool boundary are the defence;
  drift here is the main long-term risk to this decision.

Revisit this decision if: the agent proves unable to keep to the tool
boundary reliably enough to play with, or if latency at the table makes the
experience worse than a human game master reading from the book.

## Follow-up

- ADR-0003: adventure content separation (still proposed).
- ADR-0004: character state ownership — paper sheets, digital sheets, or a
  split (proposed).
- ADR-0005: concrete web stack — HTTP framework, client framework and the
  transport for streaming narration. Deliberately deferred until iteration 1
  is scoped.
- Define the initial tool surface of the dungeon master agent as part of
  iteration 1 planning.
