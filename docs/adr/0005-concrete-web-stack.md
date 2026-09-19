# ADR-0005: Concrete web stack

- **Status:** accepted
- **Date:** 2026-09-20
- **Deciders:** Maintainer
- **Supersedes:** —
- **Superseded by:** —

## Context

[ADR-0002](0002-application-form-factor.md) committed to a web application
with a Python backend in which the dungeon master is an agent with explicit
tools, and deliberately deferred the concrete stack "until iteration 1 is
scoped". Iteration 001 (#6) is now scoped — one deterministic combat encounter
against a single opponent, with the party's state on the shared screen — so
the deferral has expired.

Three questions are open: which HTTP framework runs in the Python backend,
which framework builds the client, and how streamed narration reaches the
table. They are one decision rather than three, because the transport
constrains both ends: it decides what the backend must be able to hold open
and what the client must be able to consume.

What iteration 001 actually asks of the stack is small and specific:

- a narration log that fills as the model generates, rather than in
  paragraph-sized jumps
- one input field, into which a player types a declared action and the dice
  result they rolled
- a party status panel showing the fields
  [ADR-0004](0004-character-state-ownership.md) assigns to the system, updated
  when a tool changes them
- all of it on one screen, on one machine, in one room

Three properties of the Claude Agent SDK bear on the choice. It is async
throughout: `query()` and `ClaudeSDKClient` are async iterators, so the layer
above them is async or it blocks. With `include_partial_messages` enabled it
yields `StreamEvent` objects carrying raw API events, of which
`content_block_delta` with a `text_delta` is the narration arriving token by
token. And tools registered through `create_sdk_mcp_server` run in the
backend's own process, so a tool that applies damage touches session state
directly rather than across a process boundary.

One constraint surfaced while this record was being written and changed its
shape: the maintainer wants the option of running the table's view on an iPad
later. The backend cannot follow it there — iOS does not host a long-running
Python process that spawns a subprocess for the SDK — so an iPad will always
be a client talking to a backend on the Mac at the table. That is the shape
ADR-0002 already chose. What it decides *here* is that the client must remain
replaceable without touching the backend, which rules out putting rendering
logic on the server.

## Decision drivers

- **Narration must stream.** The table visibly waits when whole paragraphs
  arrive at once, and waiting is the failure mode a human game master does not
  have.
- **Two kinds of traffic flow to the table, not one.** Narration deltas are
  text; durable state changes are structured. The status panel is fed by tool
  calls ([ADR-0002](0002-application-form-factor.md), commitment 3), never by
  reading numbers out of the narration.
- **The rules core must import neither the Agent SDK nor a web framework.**
  Whatever is chosen has to be confinable to a layer.
- **One table, one session, one machine.** No authentication, no tenancy, no
  horizontal scaling. A choice justified by any of those is justified by
  nothing here.
- **The client must be replaceable without a backend change.** The iPad path,
  and more generally the wish not to have the shared surface welded to one
  rendering technology.
- **Python is the maintainer's strongest language.** Every hour spent on
  frontend machinery is an hour not spent on the game, and the maintainer is
  the only person on this project.
- **A session lasts three hours and the connection must survive it.** A closed
  lid, a sleeping machine or a dropped wireless link must not end the evening.
- **Testable without a model and without driving a browser.** The definition of
  done requires tests; a stack whose streaming can only be checked by hand
  makes that expensive enough to skip.

## Options considered

The three questions are separable enough to argue one at a time, and the order
matters: the transport constrains the other two.

### The transport

#### Option A: Server-Sent Events for server→client, POST for player input

The client opens one `EventSource` on a session stream and receives named
events — narration deltas, party state, errors. A declared action is an
ordinary `POST`.

- Good: `EventSource` reconnects on its own and resumes with `Last-Event-ID`.
  The three-hour session survives a lid closing without a line of recovery code.
- Good: named event types are part of the protocol, so "narration text" and
  "party state changed" are distinct on the wire rather than by convention
  inside one envelope.
- Good: it is plain HTTP. `curl -N` shows exactly what the table sees, and the
  backend is testable with an ordinary ASGI test client.
- Good: a second screen — a projector, a tablet — opens the same stream. No
  additional design.
- Bad: one-directional. Player input needs a second endpoint, so what feels
  like one conversation is two routes.
- Bad: text only. Irrelevant here, because assets reach the client through the
  reveal-checking endpoint of
  [ADR-0003](0003-adventure-content-separation.md) and never through the
  narration stream.

#### Option B: WebSocket

One bidirectional connection carries narration, state and input.

- Good: symmetric and single. One connection to open, one to reason about.
- Good: the right answer if the client ever needs to send messages while the
  model is mid-generation.
- Bad: no reconnection, no resume, no heartbeat. All three are ours to build,
  and all three are exactly what a long evening needs.
- Bad: every message type and its versioning is invented here. The protocol
  offers no equivalent of a named event.
- Bad: harder to test and to inspect. A dropped or half-open socket is a class
  of bug the alternative does not have.

### The client

#### Option A: React with Vite and TypeScript

- Good: the maintainer already knows React, which in a one-person project
  outweighs most technical comparisons.
- Good: the largest ecosystem by a wide margin, which matters for the map grid
  that ADR-0002 names as a later view.
- Good: the best-trodden path to an iPad client — a progressive web app needs
  only a manifest, a packaged native shell reuses the same code, and React
  Native shares the idiom if a full rewrite is ever wanted.
- Good: TypeScript makes the wire format a checked contract rather than a
  remembered one. The fields in ADR-0004 are a boundary between two components,
  and a typo in one of them is otherwise discovered as an empty panel during a
  fight.
- Bad: a second language and a Node toolchain enter a Python project —
  `npm`, a lockfile, and dependency updates for something that is not the game.
- Bad: React carries concepts this application does not need, and the cost of
  ignoring them is not zero.

#### Option B: Svelte 5 with Vite

- Good: less boilerplate, and server-pushed state maps almost directly onto
  runes.
- Good: smaller bundle, simpler mental model.
- Bad: the maintainer does not know it. Learning a client framework is not what
  this project is for.
- Bad: a thinner ecosystem for the later map view.

#### Option C: Server-rendered HTML with htmx or Datastar

Python renders fragments; SSE patches them into the page. No client framework,
no Node.

- Good: no build step and no second language. Everything stays where the
  maintainer is strongest.
- Good: SSE is the native idiom of both libraries, so the transport and the
  client would be one decision instead of two.
- Bad: rendering logic moves into the backend. A native iPad client would then
  start from nothing, because what the backend sends is markup rather than
  state. This is the option the iPad driver rules out.
- Bad: the map grid, and interaction richer than "display and one input field",
  push against the model rather than with it.

#### Option D: Vanilla TypeScript with Vite, no framework

- Good: iteration 001's client — a log, an input, a panel — is perhaps two
  hundred lines without any framework at all.
- Good: nothing to learn, nothing to keep updated.
- Bad: the decision would be reopened at the map grid, and reopening it then
  means rewriting a client that already works. A choice that is known to be
  temporary is worse than the choice it defers to.

### The HTTP framework

#### Option A: FastAPI

- Good: ASGI and async-native, which is what the SDK's async iterator needs.
  Streaming an async generator as SSE is a `StreamingResponse`.
- Good: Pydantic. [ADR-0003](0003-adventure-content-separation.md) already
  commits to JSON Schema validation at both ends of the adventure package, the
  Agent SDK's tools take argument schemas, and the wire format needs a
  declaration too. One validation library covers all three.
- Good: the best-documented Python web framework, which for a solo maintainer
  is a real property and not a popularity argument.
- Bad: dependency injection and decorators invite business logic into route
  handlers, which is precisely the drift ADR-0002 warns about.

#### Option B: Starlette alone

- Good: smaller, no magic, and FastAPI's streaming primitives are Starlette's
  anyway.
- Bad: request validation is then hand-written, and it would be hand-written
  against the same Pydantic models FastAPI would have wired up.

#### Option C: Litestar

- Good: more consistent than FastAPI, with good SSE primitives.
- Bad: a smaller ecosystem, fewer examples, and no familiarity to draw on. It
  would win a comparison that this project is not holding.

## Decision

We choose **FastAPI in the backend, React with Vite and TypeScript in the
client, and Server-Sent Events for narration and state with ordinary `POST`
for player input**.

The reasoning that decides each, in one line: FastAPI because the backend is
async by necessity and Pydantic is already needed elsewhere; React because the
maintainer knows it and it is the shortest path to an iPad; SSE because the
traffic is asymmetric — narration and state flow continuously to the table,
while a player declares one action per turn — and because reconnection after a
three-hour evening's interruptions is a property of the protocol rather than a
feature we would have to write.

Four commitments follow, and they are the substance of the decision.

**1. The backend serves JSON and events. It never serves HTML.** The client
receives state and renders it; it is never handed markup. This is what keeps
the client replaceable — by a progressive web app on an iPad, by a packaged
native shell, or eventually by a genuinely native client — without the backend
changing at all. It is also the reason Option C above was rejected despite
fitting the maintainer's skills best.

**2. Narration and state are separate event types on the wire.** The stream
carries at least `narration_delta`, which is text, and `party_updated`, which
is the party state as the backend holds it. The status panel is rendered from
`party_updated` and from nothing else. A number that appears in the narration
is prose; a number that appears on the panel came through a tool. This is
[ADR-0002](0002-application-form-factor.md)'s third commitment made visible in
the wire format, where it can be checked rather than merely intended.

**3. The wire format is a declared contract, typed at both ends.** Pydantic
models on the backend, TypeScript types on the client. TypeScript is strict
where the wire is crossed and relaxed elsewhere; the point is the contract, not
ceremony for its own sake. The fields ADR-0004 assigns to the system are the
first thing this contract describes.

**4. The web framework lives in one layer.** The rules core imports neither
`fastapi` nor `claude_agent_sdk`, and neither does the session state module.
FastAPI appears only in the API layer that translates HTTP into calls on the
session, and the Agent SDK only in orchestration. The test for this is
mechanical and belongs in CI: an import of a web framework or the SDK below the
API layer is a build failure, not a review comment.

Two consequences of the deployment shape are settled here because they follow
directly and would otherwise be decided by accident:

**The table runs one process.** `uvicorn` serves the API and the built client
as static files; the players open a local address in a browser. Vite's dev
server exists during development and proxies to the backend, and is not part of
how the game is played.

**Reconnection is the client's job and the protocol's gift.** Events carry ids;
the browser resends `Last-Event-ID` after a drop. What the backend does with it
may start as crudely as re-sending the current party state and the last few
lines of narration. Replaying the stream exactly is a refinement, not a
precondition.

## Consequences

What becomes easy:

- Streaming narration is a short async generator over the SDK's `StreamEvent`
  messages, yielded as SSE. The backend does not accumulate text it then has to
  chunk again.
- The status panel is an event type rather than a polling loop, so it is
  correct by construction whenever a tool changes state.
- `curl -N` against the stream shows exactly what the table sees. Streaming is
  testable with an ordinary ASGI test client, with no browser and no model.
- Moving the table's view to an iPad later is a client change. A progressive
  web app needs a manifest; a packaged shell reuses the same code; even a
  native rewrite touches nothing behind the API.
- One validation library — Pydantic — covers the adventure schema, the tools'
  arguments and the wire format.

What becomes hard, and what we accept:

- A second language and a Node toolchain join the project: `npm`, a lockfile,
  and updates for dependencies that have nothing to do with D&D. This is the
  real price of choosing a client framework at all, and it is paid to keep the
  rendering off the server.
- What feels like one conversation is two routes. A reader of the code has to
  hold both halves in mind to see the loop.
- FastAPI makes it comfortable to put logic in a route handler. Commitment 4
  and its CI check are the defence; without the check it is a rule that erodes
  quietly.
- The client ecosystem moves faster than the Python one. Occasional churn that
  produces no new play is now part of the maintenance.
- The client cannot send anything to the agent while it is generating. Today
  that is correct — a turn is a turn — but see below.

What we are committed to:

- No server-rendered HTML, in any iteration, for any convenience.
- The client renders only what the backend sends it, which is how hidden
  information stays hidden ([ADR-0002](0002-application-form-factor.md)).
- The wire format is versioned and changed deliberately, like the adventure
  schema.

Revisit this decision if: a player needs to interrupt the dungeon master
mid-generation — "warte, ich mache etwas anderes" — often enough that it spoils
play, because a mid-stream message from client to server is the one thing SSE
genuinely cannot do and the one thing WebSocket is genuinely for. Revisit it
also if the map grid turns out to need interaction that React's model fights
rather than supports.

## Follow-up

- Iteration 001 issue: project skeleton — backend package layout enforcing the
  layer boundary, client scaffold, one process serving both.
- Iteration 001 issue: the SSE event contract — the event types, their payloads
  and their Pydantic and TypeScript definitions. It is the same piece of work
  as defining the agent's initial tool surface, because every tool that changes
  durable state produces an event.
- Iteration 001 issue: the CI check that fails a build importing `fastapi` or
  `claude_agent_sdk` below the API layer. Commitment 4 is otherwise aspirational.
- Backlog spike: the iPad as a client — progressive web app first, packaged
  shell only if the browser chrome is genuinely in the way. Taken up after
  iteration 001 ends in something playable.
- Not decided here: how a player interrupts a turn in progress. It is the named
  revisit signal above, and inventing a mechanism before the need is felt would
  pick the transport for the wrong reason.
