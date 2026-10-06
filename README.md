# dnd-ai-dungeon-master

An AI Dungeon Master for tabletop Dungeons & Dragons: a group of players
sits at one table with pen, paper and dice, and the AI takes the game
master's chair — narrating the adventure, playing NPCs and monsters, asking
the players what they do, and adjudicating the results they roll.

## Status

Early. Iteration 001 — one combat encounter — is under way; see
[`docs/iterations/`](docs/iterations/README.md). What exists so far: one
process that serves the API and the built client; the table's event stream,
with narration arriving word by word; a form to enter the party and a status
panel that shows it; an input for the declared action, with the acting
character preselected; the rules of combat in deterministic code; an opponent,
the SRD's Ogre, through the adventure port; and the dungeon master's tools,
which run a whole encounter against it — initiative, attacks, saving throws,
damage, turns and the outcome — with the opponent's numbers hidden from the
table. The dungeon master is a Claude agent, on your own Claude subscription
or on an API key.

## Running it

Needs Python 3.12 or newer and Node.js. All commands run from the repository
root unless they say otherwise — the backend reads `.env` from the directory
it is started in.

What runs where, and what happens between declaring an action and reading the
narration, is in [docs/runtime.md](docs/runtime.md), with diagrams.

### Once, and again after dependencies change

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
(cd client && npm ci && npm run build)
```

- `python3 -m venv .venv` creates a Python environment of the project's own in
  `.venv`, so nothing is installed into the system's Python.
- `pip install -e '.[dev]'` installs the backend *editable*: Python imports it
  straight from `src/`, so a code change needs no reinstall. `[dev]` adds the
  test tools. This also installs the Claude Agent SDK, which brings its own
  copy of the Claude Code CLI.
- `npm ci` installs the client's dependencies exactly as `package-lock.json`
  pins them; `npm run build` type-checks the client and bundles it into
  `client/dist`, which is what the backend serves at the table.

### The dungeon master's credential

See [ADR-0007](docs/adr/0007-model-credentials.md). Configuration comes from
`DM_` environment variables or a `.env` file in the repository root, which is
never committed; `cp .env.example .env` gives you every variable with an
explanation. The backend reads it once, when it starts: after changing `.env`,
restart it.

- **On your Claude subscription** (the default): log in once with Claude Code
  itself — `claude /login`, or `claude setup-token` for a long-lived token you
  export as `CLAUDE_CODE_OAUTH_TOKEN`. The application never reads that
  credential, and an `ANTHROPIC_API_KEY` in your shell is switched off for the
  dungeon master, so it cannot silently outrank the login.
- **On an API key**: create one in the Claude Console and set
  `DM_ANTHROPIC_API_KEY` in `.env`. Start in that mode with
  `DM_CREDENTIAL_MODE=api_key`, or switch between turns:

  ```bash
  curl -X PUT http://127.0.0.1:8000/api/session/credentials \
    -H 'content-type: application/json' -d '{"mode": "api_key"}'
  ```

Each turn checks which credential the CLI actually reports and stops if it is
not the chosen one. `DM_MODEL` picks the model (default `claude-opus-5`).
Without any credential, `DM_DUNGEON_MASTER=stand_in` runs a stand-in that only
echoes what you declare.

### At the table: one process

```bash
.venv/bin/uvicorn dungeon_master.api.app:app --timeout-graceful-shutdown 1
```

Then open <http://127.0.0.1:8000>.

- `uvicorn` is the web server. `dungeon_master.api.app:app` names the module
  to import and the application object in it; importing the module builds the
  whole backend — configuration, credential, opponent, dungeon master and the
  table's session.
- It listens on `127.0.0.1:8000`, so only this machine can reach it. The API
  has no authentication; do not open it to a network you do not trust.
- It serves the API under `/api` and the built client from `client/dist` (or
  `DM_CLIENT_DIST`) at `/`. Without a build it serves the API only and says so
  in its log. After changing the client, run `npm run build` again.
- `--timeout-graceful-shutdown 1`: the table's event stream stays open as long
  as a browser shows the page, and without the timeout uvicorn waits for that
  browser before it stops. With it, `Ctrl+C` stops the server after a second;
  the error it logs about a cancelled request is that open stream, and
  harmless.
- The session lives in this process's memory. Stopping it ends the session:
  the next start begins with an empty party.

### While developing: two processes

In one terminal, the backend:

```bash
.venv/bin/uvicorn dungeon_master.api.app:app --reload --timeout-graceful-shutdown 1
```

In another, the client:

```bash
cd client && npm run dev
```

Then open <http://localhost:5173>, not port 8000.

- The Vite dev server (`npm run dev`) serves the client from its source and
  updates the page the moment a client file changes, usually without a reload.
  Every request to `/api` it passes on to the backend on port 8000, so the
  page behaves as it does at the table.
- `--reload` makes uvicorn restart the backend whenever a Python file changes.
  A restart is a new, empty session. The page reconnects on its own, but keeps
  showing the old session until the new one's first event arrives: reload the
  page after a restart. Changes to `.env` are not watched; restart by hand.
- The build in `client/dist` plays no part here, and need not be current.

### Watching what happens

`curl -N` shows exactly the events the page receives (see
[the event contract](docs/event-contract.md)). In one shell:

```bash
curl -N http://127.0.0.1:8000/api/session/stream
```

and in another, declare an action:

```bash
curl -X POST http://127.0.0.1:8000/api/session/actions \
  -H 'content-type: application/json' -d '{"text": "I attack the ogre, 17"}'
```

What the model was told and answered, every tool call and its result, and the
cost are in Claude Code's session transcripts; where they are and how to read
them is in [docs/runtime.md](docs/runtime.md#where-to-look). With
`DM_DUNGEON_MASTER=stand_in`, the stand-in answers every action by echoing it,
word by word — useful for working on the stream without a model.

### Tests

```bash
.venv/bin/pytest
(cd client && npm test && npm run lint && npm run build)
```

No test calls a model; they need no credential.

**After changing the event contract** in `src/dungeon_master/events/`,
regenerate the schema and the client's types, and commit both:

```bash
.venv/bin/python -m dungeon_master.events.schema
(cd client && npm run contract)
```

## Code layout

The backend package is layered as
[ADR-0005](docs/adr/0005-concrete-web-stack.md) commits it to be, one package
per component of the [architecture](docs/architecture.md):

| Package | Component | May import |
| --- | --- | --- |
| `dungeon_master.api` | API layer | FastAPI — the only package that may |
| `dungeon_master.orchestration` | Session orchestration | Claude Agent SDK — the only package that may |
| `dungeon_master.tools` | Tool layer | rules core, session state, events — neither a web framework nor the SDK |
| `dungeon_master.events` | The table's event contract | session state — neither a web framework nor the SDK |
| `dungeon_master.rules` | Rules core | neither a web framework nor the SDK |
| `dungeon_master.session` | Session state | neither a web framework nor the SDK |
| `dungeon_master.adventure` | AdventureRepository port, content models | rules core — neither a web framework nor the SDK |

The last five rows are enforced, not merely intended:
`tests/test_layer_boundary.py` fails on any such import, and CI runs it on
every pull request.

The client lives in `client/` (Vite, React, TypeScript), the tests for the
backend in `tests/`.

## Documentation

- [Vision and scope](docs/vision.md)
- [Architecture](docs/architecture.md)
- [The table's event contract](docs/event-contract.md) — what the shared
  screen receives, and what it sends
- [What happens when it runs](docs/runtime.md) — processes, the flow of one
  declared action, and where to look when debugging
- [Decision records](docs/adr/README.md)
- [Process](docs/process.md) — how work moves from issue to merge
- [Working agreements for AI assistants](CLAUDE.md)
- [Handover scripts](scripts/README.md) — the tooling behind the steps that
  reach GitHub

## Adventure content

This repository contains no adventure material and never will. Adventure
content is copyrighted, is kept outside this repository, and is loaded by
the application at runtime. See
[ADR-0003](docs/adr/0003-adventure-content-separation.md). CI fails a pull
request that adds adventure content paths, binaries or images, or test
fixtures without a stated provenance; see
[`scripts/README.md`](scripts/README.md#repository-guards).

## Licence

Code is licensed under the terms in [LICENSE](LICENSE).
