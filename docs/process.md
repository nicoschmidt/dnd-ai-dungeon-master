# Process

How work moves through this project, written for the maintainer.

`CLAUDE.md` holds the rules and is binding. This document is the walkthrough:
what to do next, and where to click. It links to the rules rather than
repeating them. **Where the two disagree, `CLAUDE.md` wins** — and that is a
defect to fix, not a choice to make.

## Where am I?

| What you want | What to do next |
| --- | --- |
| Start something new | Is there an issue? If not, write one. Then set it to `Ready` and create a branch. |
| An idea, but not now | Issue in `Backlog`. Do not create a branch. |
| Work was prepared in a Cowork session | Read the local branch diff, push it, open the pull request. |
| A pull request is open | Review it, tick the definition of done, merge. |
| A pull request was merged | Run the cleanup block in step 8 below, card to `Done`. |
| A decision that is hard to reverse | Write the ADR **before** the code. See `docs/adr/README.md`. |
| An iteration goal is playable | Write the retro note in `docs/iterations/`, close the epic. |
| Something feels too big | Set `Größe: L`. It must be cut before it enters an iteration. |
| You have lost the thread | Open the project board, filter `Status: In progress`. That is what is actually started. |

## What you get handed, and what you do

You own every step that reaches GitHub. You do not have to compose any of
them.

For each manual step the assistant hands over the finished artefact and the
command to run it: the issue text, the pull request body, the exact
`git`/`gh` invocation with real numbers and paths filled in. Drafted bodies
are written beside the repository (`../pr-<n>-body.md`, `../create-*.sh`),
never committed — inside the repository they would be a second task list.

So your part is: read it, judge it, paste it. If a command arrives with a
placeholder still in it, or a step arrives as an instruction rather than a
command, that is a defect — say so.

The one thing the assistant does itself is creating the local branch, because
it cannot commit without one. Nothing has reached GitHub at that point; the
push is the gate, not the branch.

## The standard cycle

1. **Issue.** Use a template: feature, bug or spike. Acceptance criteria are
   statements that can be checked, not intentions.
2. **`Ready`.** The criteria are clear enough that work could start today.
3. **Branch.** `feat/<issue>-<slug>`, `fix/…`, `docs/…`, `chore/<slug>`.
   Usually created by the assistant so it can commit; never work on `main`.
4. **Work.** Cowork for product and architecture questions; Claude Code for
   work against existing code. Rule of thumb: if answering needs the
   codebase, it belongs in Claude Code.
5. **`In review`.** Push the branch, open the pull request in the repository
   view (Code tab → "Compare & pull request"), put `Closes #<n>` in the body.
6. **Review.** Tick the template's checklist for real. Line-level changes are
   easiest as review suggestions; questions about the goal belong on the
   issue; open-ended "is this even right" belongs in a Cowork session.
7. **Merge.** You merge. The assistant never merges its own pull request.
8. **After.** Clean up and move the card to `Done` (automatic if the "Item
   closed" workflow is enabled):

   ```bash
   git checkout main && git pull
   git branch -d <branch>                  # local
   git push origin --delete <branch>       # remote, if it still exists
   git fetch --prune                       # drop stale tracking refs
   ```

   Enabling **Settings → General → "Automatically delete head branches"**
   makes the remote half of this unnecessary from then on.

## Who can do what

|  | Cowork | Claude Code | You |
| --- | --- | --- | --- |
| Read the repository | yes | yes | yes |
| Commit on a branch | yes | yes | yes |
| Push | **no — no credentials** | yes | yes |
| Open issues and pull requests | no | yes, via `gh` | yes |
| Merge | never | never | only you |

A commit made in a Cowork session is not delivered until you push it. That
missing credential is the review gate, not an inconvenience to work around.

Cowork can read a single issue or pull request by URL, but not GitHub's list
and search pages. Paste the direct link.

## When something goes wrong

**Branch has fallen behind `main`**

```bash
git checkout main && git pull
git checkout <branch> && git rebase main
```

**You committed on `main` by accident** — do not push. Rescue the work onto a
branch and reset:

```bash
git branch <rescue-branch>          # keeps the commits
git reset --hard origin/main        # main back to the remote state
git checkout <rescue-branch>
```

**Two pieces of work want the same file.** Put them on one branch and say so
in the pull request, or finish the first and rebase the second. Parallel
branches touching the same file are a conflict you schedule for yourself.

**An iteration keeps growing.** Cut the goal, move the remainder to issues.
Iterations here are bounded by scope, not time, so nothing else stops the
growth.

**You notice a decision was made without an ADR.** Stop, write it, then
continue. An ADR written afterwards is worth much less, because the options
not taken are already forgotten.

**An adventure file has landed in this repository.** Remove it before the
commit is pushed. If it was already pushed, the history has to be rewritten —
and that is a genuinely bad afternoon, which is why the rule exists.

## Conventions at a glance

- **Task list:** GitHub issues only. No markdown backlogs, no TODO files.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`,
  `chore:`). The message carries the reasoning; discussion in a chat window
  does not survive.
- **Language:** repository in English, conversation in German.
- **Adventure content** never enters this repository. See
  [ADR-0003](adr/0003-adventure-content-separation.md).
