# Iterations

An iteration is a milestone: `NNN <short goal>`, its goal in the description,
its scope the issues in it. The open milestones are the plan; the current
iteration is the open one with the lowest number. The rules are in
`.claude/rules/process/iterations.md`.

This folder holds what a milestone cannot: one retro per finished iteration,
named `NNN-<short-goal>.md` and copied from [TEMPLATE.md](TEMPLATE.md) when the
milestone closes. What shipped, what was added or moved on, and what the
iteration taught.

The larger aim the iterations work towards, the MVP, is in
[docs/vision.md](../vision.md).

## Files written before iterations were milestones

Until ai-dev-process 0.3.0 an iteration was planned in its file here and
tracked on a project board, with an epic issue for its scope. Those files
keep their structure:

- The iterations up to 001a are finished. Their files are their retros, and
  the epics they name are closed.
- [002](002-one-scene-from-our-adventure.md) and
  [003](003-one-evening-of-play.md) were written as plans, before their
  iterations started. They stay as they are; **Result** and **Process
  learnings** are filled in when the milestone closes. Where such a file and
  its milestone disagree about scope, the milestone is right.

## The iterations so far

| Iteration | Goal in brief | Proves, or learned |
| --- | --- | --- |
| [001](001-one-combat-encounter.md) | One combat encounter against one opponent | The engine: streaming, the tool boundary, deterministic rules, the party panel |
| [001a](001a-the-table-screen.md) | A table screen for an evening of play | The table: state in view, the group's language, a party that is saved |
| [002](002-one-scene-from-our-adventure.md) | One scene from the maintainer's own adventure | The content boundary: schema, loader, hidden and revealed information |
| [003](003-one-evening-of-play.md) | One evening through one chapter | Ingest from the scan, scene progression, resuming after a restart; planned to reach the MVP |

An iteration found to be needed between two others takes the number before it
with a letter, like 001a. Numbers are referred to from ADRs, code and issues,
so they are never shifted.

Status is not kept here. Which issues are open or done, and which iteration
they belong to, is read from the issues and their milestones.
