# ADR-0006: A separate game master view, fed by a session journal

- **Status:** accepted
- **Date:** 2026-09-26
- **Deciders:** Maintainer
- **Supersedes:** —
- **Superseded by:** —

## Context

[ADR-0002](0002-application-form-factor.md) made hidden state the reason for
having a backend at all, and [ADR-0005](0005-concrete-web-stack.md) made it a
property of the wire: the client renders only what the backend sends. Nothing
outside the fiction reaches the table.

Two needs push against that, and #20 asked about the first:

- **A table without a human game master cannot check the arithmetic.** At a
  normal table the numbers sit behind a screen, and behind the screen is a
  person who can be asked. Here nobody can be asked, and a wrong subtraction is
  invisible.
- **The maintainer cannot debug what cannot be seen.** Iteration 001 moves
  combat into code while the model still decides what to call. When the ogre
  hits for 40, the question is whether the model passed the wrong argument, the
  code computed wrongly, or the narration contradicted a correct result. Without
  a record of what was called with what, and what came back, all three look the
  same.

The maintainer asked for more than #20 did: a view of everything the system and
the dungeon master know — adventure information the party has not discovered,
the agent's plan, opponent state, the history of every roll and computation —
and a log of every tool call, whether or not it appears on a screen.

Three properties of the environment bear on the shape. The Agent SDK already
exports OpenTelemetry — spans per model request and tool call, token and cost
counters — when told to by environment variables; its tool content is opt-in
and its console exporter is unusable, because the SDK talks to the CLI over
standard output. Tools registered with the SDK run in the backend's own process
([ADR-0005](0005-concrete-web-stack.md)), so our tool layer sees every call
with its arguments and its result before the SDK does anything with it. And the
records in question contain adventure text, which
[ADR-0003](0003-adventure-content-separation.md) keeps out of this repository
and out of every dump.

## Decision drivers

- **The table's stream must stay structurally clean.** Hidden information that
  reaches the table by a rendering mistake is the one failure ADR-0002 exists
  to prevent. A design that relies on the client choosing not to show something
  is not a design.
- **What happened must be reconstructable after the fact** — during a session,
  after it, and in a test.
- **The record must be in domain terms.** "The code rolled 14 + 6 against AC
  16" answers a question; a span named `claude_code.tool` with a duration does
  not.
- **Testable without a model.** The same requirement as every other layer.
- **One person, one machine.** No hosted observability stack to run, pay for or
  keep patched — and none that would receive adventure text.

## Options considered

### How the view reaches a screen

#### Option A: Nothing outside the fiction

- Good: the simplest guarantee there is.
- Bad: leaves both needs above unanswered. Debugging by reading narration is
  guessing.

#### Option B: An out-of-fiction panel in the table's view

The shared screen gains a panel — rolls, opponent state — that the group can
open.

- Good: one screen, one client, nothing new to open.
- Bad: hidden information travels on the table's stream and the client decides
  not to show it. That is exactly the "hidden by convention" ADR-0002 rejected.
- Bad: at a table where everybody is a player, a panel on the shared screen is
  seen by everybody the moment one person opens it.

#### Option C: A separate view with its own stream

A route of its own in the same client (`/gm`), fed by a stream of its own. The
table's stream carries no hidden event type at all.

- Good: the table's guarantee holds by construction and can be tested: the set
  of event types the table's stream may carry is a list, and a test fails on
  anything else.
- Good: whoever needs it opens it deliberately — the maintainer on a laptop
  while debugging, or the group, together, when a result is disputed.
- Bad: a second stream and a second view to build and maintain.

### Where the record comes from

#### Option D: The SDK's OpenTelemetry export as the only record

- Good: already built; spans, tokens, cost and latency for free.
- Bad: it records calls, not meaning. It does not know that a roll was an
  attack, what the armour class was, or which state changed.
- Bad: tool arguments and results are opt-in, the tracing is marked beta, and a
  collector becomes a precondition for seeing anything at all.

#### Option E: Our own journal, written by the tool layer

Every tool call, every roll, every state change and every plan update is
appended as a structured record to a file per session.

- Good: in domain terms, because the tool layer is where the domain is.
- Good: deterministic and testable — a test runs a tool and reads the record.
- Good: the game master view renders from it, so the view and the record
  cannot disagree.
- Bad: one more thing to write, and it knows nothing about latency inside the
  SDK.

## Decision

We choose **Option C with Option E**, and keep the SDK's OpenTelemetry export
as an optional second layer.

**1. The session journal is the record.** An append-only JSON Lines file per
session, written by the tool layer and by orchestration. It holds:

- every tool call: name, arguments, result or refusal, the events it produced,
  duration
- every roll the code makes: purpose, dice expression, the individual dice,
  modifier, mode, total — and the session's random seed at the start
- every state event, whichever stream carries it
- every update of the agent's plan
- per model turn: model, token usage, cost as the SDK reports it, latency,
  errors, and which credential mode was active
  ([ADR-0007](0007-model-credentials.md))

The journal lives outside the repository, at a configured path. It contains
adventure text and is therefore under the same rule as the adventure package
([ADR-0003](0003-adventure-content-separation.md)): never committed, never
attached to an issue, never embedding an asset.

It is a record, not persistence. Whether a session is later restored by
replaying it is a separate decision that this one neither makes nor forecloses.

**2. The game master view is a separate route with its own stream.** `/gm` in
the same client, fed by its own SSE stream. The table's stream has a closed list
of event types; the hidden ones — opponent state, roll records, tool calls, the
plan, and from iteration 002 undiscovered adventure information — exist only on
the game master's stream. A test fails if the table's stream can emit anything
not on its list. The view renders from the journal's records and from nothing
else.

There is no authentication, in keeping with
[ADR-0005](0005-concrete-web-stack.md): anyone at the table who types the
address can open it. The risk is a spoiler, not a breach, and the group decides
what to look at. A configuration switch turns the stream off entirely.

**3. The agent's plan is explicit state.** The dungeon master writes what it
intends — next steps, what it is holding back, what it expects the party to do
— through a tool, and that is what the view shows. Nothing is extracted from the
model's reasoning. A plan written through a tool can be journaled, tested and
compared with what happened; reasoning text can do none of that.

**4. OpenTelemetry is optional and local.** The SDK's export is switched on by
environment variables when latency needs explaining, and points at a collector
on the same machine. Tool content and raw API bodies are only ever exported to
that local collector, because they carry adventure text. It is not a
precondition for anything, and nothing in the game master view depends on it.

This answers #20: yes, there is a view outside the fiction, and it is not on
the shared screen unless the group puts it there.

## Consequences

What becomes easy:

- A disputed result is looked up, not argued about: the roll, the armour class
  and the damage are in one record.
- A test of a tool asserts on the journal record it produced, which makes the
  record part of the contract rather than a side effect.
- The question "did the model call the wrong tool, or did the code compute
  wrongly?" has an answer for every turn.
- Cost per session and per turn is visible from the first iteration, which
  matters when the subscription's limits and an API key's bill are both in
  play ([ADR-0007](0007-model-credentials.md)).

What becomes hard, and what we accept:

- Two streams and two views. The table's view stays small; the game master
  view grows with every iteration that adds hidden information.
- The journal format is a contract of its own. It changes deliberately, like the
  wire format, and a test that reads records breaks when it does.
- A plan tool is one more thing the model can forget to call. An empty plan in
  the view is itself a signal worth having.
- A journal full of adventure text is a new place for that text to leak from.
  The configured path, the `.gitignore` and the content check in CI (#5) are the
  defence.

What we are committed to:

- The table's stream carries a closed list of event types, enforced by a test.
- Every tool call is journaled, whether or not any view shows it.
- No hidden information is extracted from the model's reasoning; if the view
  shows it, a tool produced it.

Revisit this decision if: the group opens the game master view during play often
enough that it has become part of the table's surface — then some of it belongs
on the shared screen, deliberately; or if the journal is chosen as the basis for
persistence, which would make its format a much harder contract.

## Follow-up

- Iteration 001 issue: the session journal.
- Iteration 001 issue: the game master view — opponent state, roll records, tool
  calls, the plan, cost per turn.
- Undiscovered adventure information joins the view in iteration 002, when
  there is an adventure.
- Not decided here: whether a session is restored from the journal.
