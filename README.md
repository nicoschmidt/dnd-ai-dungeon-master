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
the SRD's Ogre, through the adventure port; and the dungeon master's tools, of
which damage, healing, temporary hit points and conditions on characters work
so far. Until the agent runs on a model, a stand-in answers.

## Running it

Needs Python 3.12 or newer and Node.js. All commands run from the repository
root unless they say otherwise.

Once, and again after dependencies change:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
(cd client && npm ci && npm run build)
```

**At the table**, one process serves everything:

```bash
.venv/bin/uvicorn dungeon_master.api.app:app --timeout-graceful-shutdown 1
```

Then open <http://127.0.0.1:8000>. The backend serves the client from
`client/dist`; set `DM_CLIENT_DIST` to serve a build from elsewhere. Without a
build it serves the API only and says so in its log.

The timeout matters: the table's event stream stays open as long as a browser
shows the page, and without it uvicorn waits for that browser before it stops.

**While developing**, run the backend and the Vite dev server side by side,
and open <http://localhost:5173>. Vite proxies `/api` to the backend.

```bash
.venv/bin/uvicorn dungeon_master.api.app:app --reload --timeout-graceful-shutdown 1
```

```bash
cd client && npm run dev
```

**Watching the stream.** `curl -N` shows exactly the events the page receives
(see [the event contract](docs/event-contract.md)). In one shell:

```bash
curl -N http://127.0.0.1:8000/api/session/stream
```

and in another, declare an action:

```bash
curl -X POST http://127.0.0.1:8000/api/session/actions \
  -H 'content-type: application/json' -d '{"text": "I attack the ogre, 17"}'
```

Until the dungeon master runs on a model (#32), a stand-in answers every
action by echoing it, word by word.

**Tests:**

```bash
.venv/bin/pytest
(cd client && npm test && npm run lint && npm run build)
```

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
