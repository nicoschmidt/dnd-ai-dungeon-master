# ADR-0007: The agent runs on the maintainer's subscription or on an API key, switchable

- **Status:** accepted
- **Date:** 2026-09-26
- **Deciders:** Maintainer
- **Supersedes:** —
- **Superseded by:** —

## Context

The dungeon master runs through the Claude Agent SDK
([ADR-0002](0002-application-form-factor.md)), which runs the Claude Code CLI as
a child process. Something has to pay for the model calls, and there are two
candidates: the maintainer's Claude Pro subscription, which is already paid for,
and an API key from the Claude Console, billed per token.

The maintainer wants to start on the subscription and be able to switch to an
API key at any time — not as a later migration, but as a choice available from
the first iteration.

Four facts shape the decision.

**Anthropic's terms draw a line, and it is not where a first guess would put
it.** As of this record, Anthropic's documentation says that developers building
products or services with the Agent SDK should use API key authentication; that
third-party developers may not offer claude.ai login in their own applications,
nor route requests through subscription credentials on behalf of their users;
and that developers may not collect, store or intermediate claude.ai credentials
— sign-in must complete through Anthropic's own flow. The same documentation
says that the advertised limits of the Pro and Max plans assume ordinary,
individual usage of Claude Code and the Agent SDK.

This application has one user: the maintainer, on his own machine, with his own
subscription, for a game at his own table. Nobody else signs in, and nobody's
usage is routed through anyone else's account. The reading this record adopts is
that this is individual use of the Agent SDK. It is a reading, not a ruling, and
the consequences below are built so that it can be abandoned in one
configuration change.

**The CLI decides which credential wins, not the application.** When several are
present it uses, in order: an `ANTHROPIC_AUTH_TOKEN`, an `ANTHROPIC_API_KEY`, an
API key helper, a `CLAUDE_CODE_OAUTH_TOKEN`, and last the login stored by
`claude /login`. An API key anywhere in the environment silently beats the
subscription.

**The Python SDK passes the backend's environment on to the CLI**, with its own
`env` option merged on top. A key exported in the maintainer's shell for some
other project reaches the dungeon master unless the backend removes it.

**A subscription has usage limits that reset on a schedule.** A long evening can
reach one. An API key has no such limit, only a bill.

## Decision drivers

- Stay inside Anthropic's terms, and make the reading of them visible rather
  than implicit.
- The application never touches a subscription credential: it neither asks for
  one, stores one, nor passes one along.
- The credential in use is a fact the maintainer can see, not an assumption.
- A reached limit must not end the evening.
- Nothing about credentials enters the repository, the journal or a log.

## Options considered

### Option A: API key only

- Good: unambiguous under the terms; no limits mid-session.
- Bad: every test game costs money from the first day, while a subscription
  that could carry them is paid for anyway.

### Option B: Subscription only

- Good: no extra cost.
- Bad: rests entirely on a reading of the terms, with no way out short of a code
  change if the reading turns out wrong.
- Bad: a reached limit ends the evening.

### Option C: Both, selected by configuration, switchable between turns

- Good: starts free, and the way out is a setting.
- Good: a reached limit becomes a switch in the game master view instead of the
  end of the session.
- Bad: two paths to keep working, and a precedence rule in the CLI that has to
  be actively defeated for the subscription path to mean what it says.

## Decision

We choose **Option C**.

**1. Two modes, one at a time.** A configuration value selects `subscription`
or `api_key`. `subscription` is the default.

**2. The backend builds the credential environment of the CLI explicitly.**

- In `subscription` mode it removes `ANTHROPIC_API_KEY`,
  `ANTHROPIC_AUTH_TOKEN` and any API key helper from what the CLI receives, so
  that the CLI falls through to the maintainer's own login. That login is
  created and renewed by Claude Code itself (`claude /login`, or a
  `CLAUDE_CODE_OAUTH_TOKEN` the maintainer sets in his own shell with
  `claude setup-token`). The application never reads, stores or asks for it.
- In `api_key` mode it passes the key from its own configuration — an
  environment variable, or an `.env` file outside version control — and nothing
  else.

**3. The credential in use is verified, not assumed.** At the start of each
agent session the backend reads which credential source the SDK reports and
compares it with the configured mode. A mismatch stops the turn with an error,
rather than running on a credential nobody chose. The active mode is shown in
the game master view and written to the journal with every model turn
([ADR-0006](0006-game-master-view-and-session-journal.md)) — the mode, never the
credential.

**4. The mode can change between turns.** Switching takes effect at the next
model turn, without restarting the session. When a turn fails because the
subscription's limit is reached, the error says so and names the switch.

**5. The application never offers a login.** No login form, no OAuth flow, no
field for a token. If the application is ever run by anyone other than the
maintainer, `subscription` mode is removed and `api_key` is the only mode.

## Consequences

What becomes easy:

- Development and test games run on a subscription already paid for.
- A reached limit costs a click, not the evening.
- Moving to an API key permanently is a configuration change.
- Cost per turn is visible in both modes — as billed with a key, as an estimate
  on the subscription — so the choice between them can be made on numbers.

What becomes hard, and what we accept:

- The backend has to defeat the CLI's precedence rule deliberately, and a test
  has to prove it does: an API key in the backend's own environment must not
  reach the CLI in `subscription` mode.
- The subscription path rests on a reading of Anthropic's terms. This record
  states the reading so that it can be checked, and is the place to change it.
- Resuming an agent session under a different credential is expected to work,
  because the SDK keeps session history locally; the implementing issue has to
  confirm it rather than assume it.

What we are committed to:

- No credential in the repository, the journal, a log or an error message.
- No login flow in this application, in any iteration.
- `api_key` as the only mode the moment a second person runs the application.

Revisit this decision if: Anthropic's terms change; anyone other than the
maintainer runs the application; or the subscription's limits interrupt play
often enough that `api_key` has become the real default.

## Follow-up

- Iteration 001 issue: run the agent on the subscription or on an API key,
  switchable between turns, with the credential source verified at session
  start.
- The switch appears in the game master view (iteration 001 issue for the view).
