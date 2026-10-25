# Scripts

Two kinds live here.

**`scripts/process/`** is managed by
[ai-dev-process](https://github.com/nicoschmidt/ai-dev-process) and never
edited in this repository (`.claude/rules/process/`, `.ai-dev-process.lock`):
the board helpers behind every handover, idea capture, labels, the check that
managed files are unchanged, and their stand-in tests.

```bash
bash scripts/process/show-board.sh                   # every board field and option, read-only
bash scripts/process/set-issue-fields.sh 13 S Backlog
bash scripts/process/capture-idea.sh "<title>"       # an issue labelled idea
bash scripts/process/check-kit.sh                    # managed files unchanged
bash scripts/process/test-gh-board.sh
```

The board helpers need the `project` scope, which `gh auth login` does not
grant:

```bash
gh auth refresh -s project
```

**Everything else here** belongs to this project.

## Repository guards

These guard the repository itself and run in CI on every pull request:

| Script | What it does |
| --- | --- |
| `check-no-adventure-content.sh` | Fails on adventure content paths, binaries, images and documents, and fixture directories without provenance. Read-only. |
| `adventure-content-allowlist.txt` | The binary, image and document files that may be committed anyway. One path per line, each with a `# justification`. |
| `test-check-no-adventure-content.sh` | Exercises the check against throwaway repositories. |

```bash
bash scripts/check-no-adventure-content.sh
```

The check is a heuristic, not a proof. It cannot tell whether a paragraph was
copied out of a book ([ADR-0003](../docs/adr/0003-adventure-content-separation.md)).
What it catches is a scan, an image or an unexplained fixture slipping in by
accident.

**Test fixtures** live in a directory named `fixtures`, for example
`tests/fixtures/`. Every such directory carries a `PROVENANCE.md` that states
where its content comes from. That is either original content written for
this project, or SRD 5.1/5.2 material, named with its CC-BY-4.0 attribution.
One `PROVENANCE.md` covers everything below its `fixtures` directory.

## What belongs here, and what does not

Tooling belongs here. Content does not. A drafted issue body, a pull request
body, or a one-off script that carries either, lives **beside** the
repository (`../pr-<n>-body.md`, `../create-*.sh`) and is never committed;
those one-off scripts source `scripts/process/gh-board.sh` from here.

## In CI

The `Scripts` job in `.github/workflows/ci.yml` checks the managed files,
runs `bash -n` over every script under `scripts/` and `.githooks/`, then every
`test-*.sh` under `scripts/`. A new harness named `test-*.sh` is picked up
without touching the workflow.
