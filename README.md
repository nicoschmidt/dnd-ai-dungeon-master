# dnd-ai-dungeon-master

An AI Dungeon Master for tabletop Dungeons & Dragons: a group of players
sits at one table with pen, paper and dice, and the AI takes the game
master's chair — narrating the adventure, playing NPCs and monsters, asking
the players what they do, and adjudicating the results they roll.

## Status

Early. Iteration 001 — one combat encounter — is under way; see
[`docs/iterations/`](docs/iterations/README.md). What exists so far is the
skeleton: a backend that serves an API and the built client from one process,
and a client that shows whether it reaches the backend.

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
.venv/bin/uvicorn dungeon_master.api.app:app
```

Then open <http://127.0.0.1:8000>. The backend serves the client from
`client/dist`; set `DM_CLIENT_DIST` to serve a build from elsewhere. Without a
build it serves the API only and says so in its log.

**While developing**, run the backend and the Vite dev server side by side,
and open <http://localhost:5173>. Vite proxies `/api` to the backend.

```bash
.venv/bin/uvicorn dungeon_master.api.app:app --reload
```

```bash
cd client && npm run dev
```

**Tests:**

```bash
.venv/bin/pytest
(cd client && npm run lint && npm run build)
```

## Code layout

The backend package is layered as
[ADR-0005](docs/adr/0005-concrete-web-stack.md) commits it to be, one package
per component of the [architecture](docs/architecture.md):

| Package | Component | May import |
| --- | --- | --- |
| `dungeon_master.api` | API layer | FastAPI — the only package that may |
| `dungeon_master.orchestration` | Session orchestration | Claude Agent SDK — the only package that may |
| `dungeon_master.tools` | Tool layer | rules core, session state |
| `dungeon_master.rules` | Rules core | neither a web framework nor the SDK |
| `dungeon_master.session` | Session state | neither a web framework nor the SDK |

The client lives in `client/` (Vite, React, TypeScript), the tests for the
backend in `tests/`.

## Documentation

- [Vision and scope](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Decision records](docs/adr/README.md)
- [Process](docs/process.md) — how work moves from issue to merge
- [Working agreements for AI assistants](CLAUDE.md)
- [Handover scripts](scripts/README.md) — the tooling behind the steps that
  reach GitHub

## Adventure content

This repository contains no adventure material and never will. Adventure
content is copyrighted, is kept outside this repository, and is loaded by
the application at runtime. See
[ADR-0003](docs/adr/0003-adventure-content-separation.md).

## Licence

Code is licensed under the terms in [LICENSE](LICENSE).
