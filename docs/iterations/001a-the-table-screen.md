# 001a — The table screen

Planned. Not started.

## Goal

The group starts an evening by loading its saved party, and plays on a table
screen in its own language that keeps the party's state in view while the
story scrolls.

## Why this slice

The encounters played at the end of [001](001-one-combat-encounter.md) showed
the engine holding up and the screen getting in the way: the party's state sat
above the narration and scrolled out of sight, the interface was English at a
German-speaking table, and the party was typed in again every evening.
[002](002-one-scene-from-our-adventure.md) brings the first adventure content;
the table should be comfortable before it does.

It is called 001a rather than taking the number 002: iterations 002 and 003
were planned ahead, and their numbers are referred to from an accepted ADR
([ADR-0006](../adr/0006-game-master-view-and-session-journal.md)), from code
and from issues. A number names an iteration; it is not renumbered.

## Scope

Epic: #68.

- #63 — the table screen: the party's state in its own pane, the narration
  scrolling on its own, the input pinned below it, a dark theme
- #64 — the table speaks the configured language: one value, `DM_LANGUAGE`,
  for the narration and every string of the client
- #65 — save the party to a file, and load it again; the file is a
  `PartyEntry` of the [event contract](../event-contract.md)

The layout follows a mockup the maintainer approved, kept outside the
repository; #63 states its substance as acceptance criteria.

## Out of scope

- The session journal (#33) and the game master view (#34): moved to 002.
- A species on each character (#66): a new field in the character state moves
  the boundary of [ADR-0004](../adr/0004-character-state-ownership.md), which
  takes an ADR first.
- Saving and resuming a session (#67): the core of
  [003](003-one-evening-of-play.md), after a decision record.
- A light theme, a language switch in the interface, languages other than
  German and English, the iPad (#25).

## If it grows

1. The table screen keeps the two panes and the pinned input, and loses the
   visual polish: colours, type, the hit point bars.
2. The language issue keeps the configured narration and covers only the
   client's strings.

The pane split is not a cut candidate: it is why this iteration exists.

## Result

To be written when the goal is reached: what shipped, what did not.

## Process learnings

<!-- Inputs: issues labelled `process` since the start, review corrections in
     the merged pull requests, issues that were cut. Mark every learning:
     [project] → a change to CLAUDE.md, through an issue here
     [generic] → the process repository: transfer the issue, or draft one -->
