# 000 — Setting up the project

Not an iteration. Nothing is playable yet, and by the rule in `CLAUDE.md` an
iteration ends when its goal is playable. `001` is reserved for the first
playable goal. This records what the setup period produced and what it taught.

## What it produced

- ADR-0001 to ADR-0003 accepted; ADR-0004 open
- `CLAUDE.md` as binding working agreements, `docs/process.md` as the
  maintainer's walkthrough, `docs/vision.md`, a derived `docs/architecture.md`
- ADR practice with template and index; issue and pull request templates
- A GitHub project board, six issues, and two full runs through the process

## What it taught

**Conditional process rules do not work.** The original rule was "do not push
to `main` once the first feature branch exists". It never took effect, because
no branch was ever created, and three commits went to `main` under it. A rule
with a precondition is a rule whose escape hatch has already been written.

**A missing credential is a stronger gate than a rule.** The Cowork session
cannot push, so nothing reached GitHub without the maintainer acting. When
git-facing work moves to Claude Code that wall becomes a habit instead — the
trade was made deliberately and is recorded in pull request #8, not discovered
later.

**Manual ownership is not manual composition.** Keeping the GitHub-facing
steps manual was right; expecting the maintainer to also *write* the issue and
pull request bodies was not. The handover contract came out of noticing that
"create an issue" is an instruction, not a deliverable.

**Rules about immutability need a scope.** "An accepted ADR is immutable"
would have forbidden redacting a personal name from a heading. The rule now
says what immutability protects: the decision, its reasoning, its consequences
— not typography, links or personal data.

**Small operational facts cost time when assumed.** GitHub numbers issues and
pull requests in one sequence, which broke a branch-naming assumption twice.
Checking beats remembering.

## What to carry into iteration 001

- Every run through the process so far moved documents. Documents do not
  conflict, do not fail tests and do not break at runtime. The process has not
  actually been tested yet; code will test it.
- ADR-0004 (character state) and ADR-0005 (web stack) block the iteration.
  Both are spikes, both are one sitting, and both are open questions rather
  than research tasks.
- The first thing worth measuring is whether a fresh session can pick the
  project up from the repository alone. If it cannot, the documentation is
  decorative.
