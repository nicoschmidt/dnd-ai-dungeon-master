# 000 — Before the process

Not an iteration. A note for the record.

ADR-0001 (record architecture decisions), ADR-0002 (application form factor)
and ADR-0003 (adventure content separation) were decided and committed
before this project used issues, branches or pull requests. They went
straight to `main`, and the pull request template with its definition of
done was never exercised on them.

We are not backfilling issues for that work: tickets created after the fact,
already closed, are archaeology nobody reads. This note is the trace
instead.

What changed as a result is in `CLAUDE.md`: committing to `main` is now
forbidden without exception, work requires an issue and a branch named
before the first edit, and the assistant does not merge its own pull
request. The rule that failed was a conditional one — "do not push to main
once the first feature branch exists" — which never took effect because no
branch was ever created. Conditional process rules are worth distrusting.

Iteration 001 is the first one planned under the new rules.
