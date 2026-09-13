# Vision

## The problem

A Dungeons & Dragons group needs a game master. Finding one, or asking the
same person to always take that role, is the most common reason a group does
not play. This project removes that constraint: the AI takes the game
master's chair so that everyone at the table can be a player.

## The experience we are building for

Everyone sits at one table. Pen, paper, character sheets and physical dice.
The AI:

- knows the adventure and holds its structure, secrets and pacing
- narrates scenes and describes what the characters perceive
- asks the players what they want to do
- receives declared actions and dice results the players rolled themselves
- adjudicates outcomes against the rules and the fiction
- plays NPCs and monsters, including their tactical decisions
- keeps track of the session state: where the party is, what they know,
  what has changed in the world

The AI does not roll for the players, does not move player characters, and
does not narrate what a player character feels or decides.

## Scope

In scope:

- One adventure at a time, played by one group, co-located at one table.
- D&D 5e rules as far as adjudication requires them.
- Session continuity: a session can end and be resumed later.
- An adventure format that a human can author and that the AI can run.
- An ingest path that turns a prepared adventure into that format.

Explicitly not in scope (for now):

- Players in different locations, with synchronised state across devices.
- Digital dice, digital character sheets, virtual tabletop or battle maps.
- Accounts, multi-tenancy, or hosting the app for other groups.
- Distributing adventure content of any kind.

## Constraints that shape the architecture

- **Content separation.** This repository is public. Adventure material
  derived from purchased books is private and is loaded at runtime from
  outside the repository. The boundary between engine and content is a real
  interface, not a convention.
- **Co-located play.** There is exactly one session, in one room, with one
  shared view. No distributed state, no per-player clients, no real-time
  synchronisation.
- **Craft over speed.** This project is also an exercise in doing software
  development properly: decisions are recorded, behaviour is tested,
  documentation is part of the change.

## What "good" looks like

A group sits down, opens the app, and plays for three hours without anyone
having to explain the tool to anyone. Afterwards they want to play again,
and nobody misses having a human game master more than occasionally.
