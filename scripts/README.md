# Handover scripts

Tooling for the steps that reach GitHub. `CLAUDE.md` requires that every such
step is handed over ready to run, and these are what make that possible.

| Script | What it does |
| --- | --- |
| `gh-board.sh` | Shared helpers. Sourced, never run on its own. |
| `show-board.sh` | Prints every field on the project board and its options. Read-only. |
| `set-issue-fields.sh` | Sets size and iteration on an issue that already exists. |
| `test-gh-board.sh` | Exercises `gh-board.sh` against a stand-in for `gh`. No credentials, writes nothing. |

Run them from the repository root:

```bash
bash scripts/test-gh-board.sh
bash scripts/show-board.sh
bash scripts/set-issue-fields.sh 13 S Backlog
```

`gh-board.sh` needs the `project` scope, which `gh auth login` does not grant:

```bash
gh auth refresh -s project
```

## What they assume

Nothing is hardcoded about who owns this project. The repository is read from
the `origin` remote of the checkout the script runs in, and the board's owner
defaults to the repository's owner. Three variables override that when the
guess is wrong:

| Variable | When you need it |
| --- | --- |
| `GH_REPO=owner/name` | Running outside a checkout, or against another repository |
| `PROJECT_OWNER=name` | The board belongs to a different owner than the repository |
| `PROJECT_NUMBER=n` | That owner has more than one board |

Without a usable `origin` remote the scripts stop and say so rather than
guessing.

## What belongs here, and what does not

Tooling belongs here. Content does not.

A drafted issue body, a pull request body, or a one-off script that carries
either, lives **beside** the repository (`../pr-<n>-body.md`,
`../create-*.sh`) and is never committed: inside the repository it would be a
second task list next to GitHub issues, which `CLAUDE.md` forbids. Those
one-off scripts source `scripts/gh-board.sh` from here.

## After changing anything here

Run `bash scripts/test-gh-board.sh`. A script that writes to GitHub is
exercised against a stand-in before it is handed over — see `CLAUDE.md`. Two
broken versions of `gh-board.sh` reached the maintainer before that harness
existed, and both would have failed on their first dry run.
