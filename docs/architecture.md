# Architecture

> This document is derived from the accepted decision records in
> `docs/adr/`. It is updated in the same commit that accepts an ADR.
> If the two disagree, the ADRs are authoritative.

## Shape

A web application with a Python backend, in which the dungeon master is an
agent with explicit tools ([ADR-0002](adr/0002-application-form-factor.md)).
The players sit at one table and share one client view. Adventure content is
private, lives in its own repository, and is loaded at runtime through a
port rather than a path ([ADR-0003](adr/0003-adventure-content-separation.md)).

```mermaid
flowchart TD
    subgraph table["At the table"]
        players["Players<br/>pen, paper, physical dice"]
        client["Web client<br/>narration log · input · party status<br/>(later: map grid)"]
    end

    subgraph backend["Backend (Python)"]
        orch["Session orchestration<br/>Claude Agent SDK"]
        tools["Tool layer<br/>the only way durable state changes"]
        rules["Rules core<br/>pure, deterministic, no model calls"]
        state["Session state<br/>party · adventure progress · what is known"]
        repo["AdventureRepository (port)<br/>+ asset endpoint with reveal check"]
    end

    model["Claude model API"]

    subgraph private["Private repository"]
        content[("Adventure package<br/>manifest · scenes · npcs · assets")]
    end

    subgraph offline["Offline, run once per adventure"]
        book["Scanned book"] --> pipeline["Ingest pipeline<br/>(public repo, no content)"]
        pipeline --> content
    end

    players <--> client
    client <--> orch
    client -->|"asset requests"| repo
    orch <--> model
    orch --> tools
    tools --> rules
    tools --> state
    tools --> repo
    repo --> content
```

## Components

**Web client.** The shared surface at the table. In the first iteration it
renders narration and takes input; the party status panel follows early, the
map grid later. It renders only what the backend sends it, which is how
hidden information stays hidden.

**Session orchestration.** Runs the dungeon master agent via the Claude Agent
SDK: builds its context, streams narration to the client, and exposes the
tool surface. This is the only component that depends on the Agent SDK.

**Tool layer.** The contract between the agent and everything durable. The
agent narrates and decides; it does not mutate state by describing a
mutation. Tool contracts are designed from the domain, so a tool can start
out backed by model judgement and later be backed by deterministic code
without anything above it changing.

**Rules core.** Ordinary Python domain logic — dice arithmetic, attack
resolution, conditions, state transitions. It imports neither the Agent SDK
nor any model client, and is tested deterministically. It grows over
iterations as responsibility moves out of the model
([ADR-0002](adr/0002-application-form-factor.md), commitment 2).

**Session state.** What must survive a restart: party state, adventure
progress, what the players have learned. Narrative texture that need not
survive stays in the model's context and is deliberately not modelled here.

**AdventureRepository.** A port, not a path. The engine asks for a scene, an
NPC or an asset by identity; the filesystem implementation resolves that
against an adventure package directory whose location comes from
configuration. Tests use an in-memory implementation with original or SRD
content, so the engine is fully testable with no private content present.

Assets never reach the client as static files. They are served by an
endpoint that checks the current reveal state first, so a map the party has
not found cannot be fetched by guessing a URL.

**Ingest pipeline.** A separate offline tool in this repository. It turns a
prepared source into an adventure package that validates against the
schemas in `schemas/adventure/`. It contains no adventure material, and its
test fixtures must be original or SRD content.

## Decisions

| Decision | ADR | Status |
| --- | --- | --- |
| Record architecture decisions | [ADR-0001](adr/0001-record-architecture-decisions.md) | accepted |
| Application form factor | [ADR-0002](adr/0002-application-form-factor.md) | accepted |
| Adventure content separation | [ADR-0003](adr/0003-adventure-content-separation.md) | accepted |
| Character state ownership | [ADR-0004](adr/0004-character-state-ownership.md) | proposed |
| Concrete web stack | ADR-0005 | not yet written |

## Open

- The v1 adventure schema is iteration work, not yet defined.
- The concrete web stack — HTTP framework, client framework, transport for
  streaming narration — is deferred until iteration 1 is scoped.
- The initial tool surface of the dungeon master agent is defined as part of
  iteration 1 planning.
