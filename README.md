# dnd-ai-dungeon-master

An AI Dungeon Master for tabletop Dungeons & Dragons: a group of players
sits at one table with pen, paper and dice, and the AI takes the game
master's chair — narrating the adventure, playing NPCs and monsters, asking
the players what they do, and adjudicating the results they roll.

## Status

Early. The foundational architecture decisions are still open; see
[`docs/adr/`](docs/adr/README.md).

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
