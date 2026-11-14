# 001b — Iterations as milestones

Milestone: [001b Iterations as milestones](https://github.com/nicoschmidt/dnd-ai-dungeon-master/milestone/1)

## Goal

Every session reads what is ready and what comes next from issues and
milestones; nothing it needs is kept on the project board.

## Result

The goal was reached. The project follows ai-dev-process 0.3.0 (#78, pull
request #79): the managed rules and helpers are at that release,
`.ai-dev-process.conf` and `CLAUDE.md` no longer name the board, the MVP is a
section of [the vision](../vision.md), and this folder's README describes
iterations as milestones.

What the board held was carried over by two handover scripts. The iterations
002 and 003 are milestones with their goals in the description; #4, #33, #34
and #35 are in 002; the epics #36 and #37 are closed with a link to their
milestone. The board showed no draft items. #18, #19 and #25 had no iteration
and are in no milestone, and the ideas #66, #67 and #77 stay ideas.

The done criterion in `CLAUDE.md`, playable at the table, measures what the
group can do and does not apply to an iteration about the way of working.
What was checked instead: the session that wrote this retro has no access to
the board and read all of its evidence from issues, milestones and pull
requests.

Nothing was added while the iteration ran. It is called 001b because it came
between 001a and 002, whose number is never shifted.

The board itself stays for now, as the maintainer's view: the maintainer
finds the list of milestones harder to survey than the board, and will see
whether the board is still of use. No session relies on it.

## Moved on

Nothing. #78 was the milestone's only issue.

## Process learnings

Inputs: no issue was labelled `process` since the milestone was created. One
pull request was merged, #79, with two commits by one author, no review and no
comment; CI passed. Its definition of done was merged with "The full test
suite passes" unticked: the chat session that prepared it could not run the
backend and client suites, and CI did. Nothing moved on. Each learning marked
`[generic]` is an issue in the process repository, nicoschmidt/ai-dev-process.

- [generic] The upgrade is work like any other, and under 0.3.0 that means an
  issue in a milestone and a branch that carries its number. The upgrade path
  says "with an issue and its branch" and names no milestone for it. A session
  without credentials has neither: here the commits were made on a provisional
  branch, a handover script created the issue and renamed the branch, and the
  maintainer asked for a milestone, which then needed this retro. Process
  issue: "An upgrade names its milestone, and hands over its issue and branch".
- [generic] Iteration 003 had one open item on the board, its own epic, which
  was also the MVP epic. The upgrade path gives an MVP epic to the vision and
  a milestone only to an iteration with open issues, so the goal and the
  known needs of 003 would have been kept in a closed epic alone. The
  maintainer asked for a milestone that carries them. The path also asks for
  a milestone "of the same title" as the board's iteration; the board's
  titles were short and German ("002 Szene"), and the milestones took the
  titles of the iteration files instead. Process issue: "The upgrade from a
  board says what becomes of a planned iteration without issues".
- [generic] The four issues of 002 became ready by being put into their
  milestone, because the board showed them as `Ready`. Nobody checked them
  against the definition of ready as it now reads: none was looked at for a
  `Needs:` line that names issues. The epic of 002 had #33 first; the new
  rule for the next issue picks the lowest number, #4. What follows here:
  the four issues get their `Needs:` line before 002 starts, which changes
  nothing in the repository and so needs no issue of its own. Process issue:
  "Issues carried over from a board are checked against the new definition
  of ready".
- [project] The maintainer keeps the board as a view and decides later
  whether it is of use. Nothing in `CLAUDE.md` changes; the retro of 002 says
  whether the board was opened at all.

What worked and stays: the installer's output as a commit of its own, apart
from what the project owns, made the pull request readable; and both handover
scripts, rehearsed against a stand-in with a failure halfway and a second
run, needed no correction.
