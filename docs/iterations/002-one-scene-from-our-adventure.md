# 002 — One scene from our own adventure

Planned. Not started.

## Goal

The group plays one scene from the maintainer's own adventure: the AI reads the
boxed text aloud, keeps the game master's secrets, voices an NPC, reveals what
the party discovers, and can lead into a fight run by the engine from 001.

## What it proves

That the boundary between engine and content from
[ADR-0003](../adr/0003-adventure-content-separation.md) holds in practice: a
package from the private repository, validated against a public schema, loaded
through the port, with hidden and revealed information kept apart by structure
rather than by the model's discretion.

## Scope so far

Epic: #36.

- #33 — the session journal, first: the encounters of 001 were played on
  plausibility, and from 002 on the journal carries adventure text, so it is
  kept like the package ([ADR-0003](../adr/0003-adventure-content-separation.md))
- #34 — the game master view
- #4 — the v1 adventure schema
- #35 — the shape of the ingest pipeline (an ADR before any pipeline code)

#33 and #34 moved here from [001](001-one-combat-encounter.md), whose goal was
playable without them. Iteration [001a](001a-the-table-screen.md) comes between
the two.

Content work for this iteration may run while 001 is still open — the
maintainer decided so on 2026-09-26, pipeline code included. The issues still
belong to 002. The risk is known: 001 is the less exciting of the two, and an
iteration that is left half-done because the next one is more interesting is
the failure this note exists to name.

Expected further issues, written when the schema and the pipeline ADR exist:
loading a package through the filesystem implementation of the port, the reveal
mechanism, the adventure's hidden information in the game master view
([ADR-0006](../adr/0006-game-master-view-and-session-journal.md)), and one scene
brought from the scan into a package — by the pipeline, corrected by hand where
it falls short.

## Out of scope

- More than one scene, and moving between scenes.
- Persistence across a restart.
- Images and maps on the table's screen. Assets may be in the package; showing
  them waits.
- A fully automatic pipeline. A scene that needed hand correction still counts.

## Result

To be written when the goal is playable.
