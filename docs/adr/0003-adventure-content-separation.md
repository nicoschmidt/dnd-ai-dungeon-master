# ADR-0003: Adventure content separation

- **Status:** proposed
- **Date:** 2026-09-13
- **Deciders:** Nico Schmidt
- **Supersedes:** —
- **Superseded by:** —

## Context

This repository is public. The first adventure will be derived from a
commercially published adventure book that Nico owns, by scanning it. That
material is copyrighted: it may be used privately, but it must never be
published, and it must therefore never enter this repository or any build
artefact derived from it.

At the same time the application is useless without adventure content, so
the boundary between engine and content has to be a real, designed
interface rather than a habit that holds until someone forgets.

Two distinct concerns hide behind one word:

- **Ingest:** turning a scanned book into a structured adventure file. This
  happens once per adventure, offline, and is a separate tool from the game.
- **Runtime:** the application loading such a file while a session is played.

## Decision drivers

- No copyrighted material in the public repository, ever — including OCR
  text, derived summaries, fixtures and example prompts.
- A contributor or an AI assistant should find it hard to violate that by
  accident, not merely be asked not to.
- The engine must be testable without any private content present.
- Setup must stay simple enough for one person at one table.

## Options considered

### Option A: Local directory, path given by configuration

Content lives in a directory outside the repository; its path comes from an
environment variable or config file. The path is git-ignored.

- Good: simplest possible mechanism; no additional infrastructure.
- Good: the content never has a representation inside the repository.
- Bad: no versioning or backup of the content unless arranged separately.
- Bad: nothing structurally prevents someone copying a file in; only
  `.gitignore` and discipline.

### Option B: Private repository, consumed as a sibling checkout

Content lives in its own private Git repository, cloned next to this one.
The engine reads it through the same configured path.

- Good: content is versioned and backed up, with its own history.
- Good: clear ownership boundary; visibility is enforced by GitHub.
- Bad: a second repository to manage.

### Option C: Private repository as a Git submodule

As B, but referenced from this repository as a submodule.

- Good: one clone command, version pinning between engine and content.
- Bad: the submodule reference is visible in the public repository — the
  private repository's existence and name leak, though not its content.
- Bad: submodules are a recurring source of confusion in tooling and CI.

### Option D: Encrypted content committed to the public repository

Content encrypted at rest (e.g. git-crypt, age), decrypted at runtime.

- Good: one repository, one clone.
- Bad: publishes the ciphertext of copyrighted material permanently and
  irrevocably; a key leak is unrecoverable because history cannot be
  retracted from forks.
- Bad: rejected on risk grounds, not convenience.

## Decision

_Open. Option B is the current favourite; to be confirmed together with
ADR-0002, since the deployment shape decided there determines how content
reaches the running application._

## Open questions to resolve before deciding

1. Does the adventure format need to be versioned alongside the engine, or
   can it be loosely coupled behind a schema with a version field?
2. Where does the ingest pipeline live — in this repository (it contains no
   content, only the tool) or with the content?
3. What do test fixtures use instead of real content: hand-written original
   adventures, or SRD 5.1/5.2 material under CC-BY-4.0?
4. What safeguard beyond `.gitignore` is worth the effort — a pre-commit
   check, a CI check, or naming conventions alone?

## Consequences

_To be written with the decision._
