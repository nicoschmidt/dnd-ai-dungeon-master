# 001a — The table screen

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
- #72 — dice shortcuts beside the input: enter a roll, or let the screen roll
  it. Added during the iteration, after #63 had shipped; it moves the non-goal
  "Digital dice" out of the [vision](../vision.md)

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

The goal was reached. The group started an evening from a saved party and
played it on the new screen, without anyone explaining the tool.

Shipped:

- the table screen: the party's state in its own pane, the narration
  scrolling on its own, the input pinned below it, a dark theme (#63)
- the table in the configured language, German by default: the narration and
  every string of the client, from one value, `DM_LANGUAGE` (#64)
- the party saved to a file and loaded again; the file is a `PartyEntry` (#65)
- dice shortcuts beside the input, to enter a roll or let the screen roll it
  (#72). It was added during the iteration, after #63 had shipped, and took
  "Digital dice" out of the vision's non-goals: a roll the screen makes at a
  player's click is the player's roll

Nothing was cut. The cut order above was not needed.

What the iteration left as it is: in review, the file buttons became "Save
party" and "Load party". In German, the download in the header and the
dialog's button that enters the party now both read "Gruppe speichern". They
are never usable at the same time, because the dialog is modal, and so they
stay as they are.

## Process learnings

Inputs: no issue was labelled `process` during 001a. Four pull requests were
merged: #71, #73, #74 and #75. None carries a review comment. Two carry more
than one commit. In #71, the second commit rebuilt the screen to the design
details that arrived as a comment on #63. In #75, the maintainer renamed the
file buttons and fixed the test that named them. Nothing was cut, and #72 was
added. Each learning marked `[generic]` is an issue in the process
repository, nicoschmidt/ai-dev-process.

- [generic] #63 was built twice. The details of the approved mockup came as a
  comment after the first implementation was done, and the second commit
  redid the screen to them. For an issue that changes what the users see, the
  definition of ready does not ask for the visual reference. Process issue:
  "A user-facing issue is ready only with its visual reference".
- [generic] #72 was added while the iteration ran. `iterations.md` says how
  scope is cut, not how it is added. The addition was recorded by hand in
  this file, in the epic and in the vision. Process issue: "Adding scope to a
  running iteration has no rule".
- [generic] The review correction in #75 left a trace because it was made as
  commits on the pull request's branch ("change button text", "fix test"). A
  comment that the assistant applies would have left none. Added as a comment
  to nicoschmidt/ai-dev-process#6.
- [generic] GitHub rewrites the commits when it merges a pull request, so
  `git branch -d` refuses the merged branch. Cleaning up took a check that the
  branch and `main` did not differ, then `git branch -D`. The handover ends
  with the pull request and gives no command for the cleanup after the merge.
  Process issue: "The handover gives no cleanup command for after the merge".
- [project] Each change to the screen was checked in a browser against a
  stand-in event stream with a fight in progress. The stream was written for
  that purpose and kept in a scratch directory. It was written twice, because
  the directory was emptied in between. As tooling it belongs in the
  repository, and `CLAUDE.md`'s commands would name it. Captured as an idea:
  "A stand-in stream with a fight in progress, to look at the screen".
