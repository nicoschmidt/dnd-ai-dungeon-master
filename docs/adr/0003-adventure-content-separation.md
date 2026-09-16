# ADR-0003: Adventure content separation

- **Status:** accepted
- **Date:** 2026-09-16
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

- **Ingest:** turning a scanned book into a structured adventure. This
  happens once per adventure, offline, and is a separate tool from the game.
- **Runtime:** the application loading such an adventure while a session is
  played.

Content is not only text. Maps, NPC portraits and handouts will follow, and
the format must not have to be redesigned when they do.

## Decision drivers

- No copyrighted material in the public repository, ever — including OCR
  text, derived summaries, fixtures and example prompts.
- A contributor or an AI assistant should find it hard to violate that by
  accident, not merely be asked not to.
- The engine must be testable without any private content present.
- Hidden information is structural, not incidental (ADR-0002): the format
  must distinguish what players may see from what only the dungeon master
  knows, rather than leaving that to the agent's discretion.
- The private repository's history is only useful if its diffs are readable.
- Setup must stay simple enough for one person at one table.

## Options considered

### Option A: Local directory, path given by configuration

- Good: simplest possible mechanism; no additional infrastructure.
- Bad: no versioning or backup of the content unless arranged separately.

### Option B: Private repository, consumed as a sibling checkout

Content lives in its own private Git repository, cloned next to this one.
The engine reads it through a configured path.

- Good: content is versioned and backed up, with its own history.
- Good: visibility is enforced by GitHub, not by discipline.
- Bad: a second repository to manage.

### Option C: Private repository as a Git submodule

- Good: one clone command, version pinning between engine and content.
- Bad: the submodule reference is visible in the public repository — the
  private repository's name leaks, though not its content.
- Bad: submodules are a recurring source of tooling and CI confusion.

### Option D: Encrypted content committed to the public repository

- Bad: publishes the ciphertext of copyrighted material irrevocably; a key
  leak cannot be undone because forks keep the history. Rejected on risk
  grounds, not convenience.

## Decision

We choose **Option B**, with the split drawn as follows.

**The public repository holds the tooling and the contract.** The ingest
pipeline, the schemas, the validator and all engine code live here. None of
them contain adventure material; they describe its shape.

**The private repository holds one adventure package per adventure.** Only
extracted data and assets, nothing else.

### An adventure is a package, not a file

JSON is the format. A single JSON file is not the unit. An adventure package
is a directory:

```
my-adventure/
├── adventure.json          # manifest: schema version, id, title, index
├── scenes/
│   ├── 01-the-tavern.json
│   └── 02-the-cellar.json
├── npcs/<id>.json
├── monsters/<id>.json
├── items/<id>.json
└── assets/
    ├── maps/cellar.png
    └── portraits/the-baron.jpg
```

Three reasons for a directory rather than one file:

1. **Assets.** Images cannot live in JSON without base64 bloat that destroys
   diffs and repository size.
2. **Readable history.** The pipeline emits the package programmatically. If
   it emitted one large file, every re-run would look like a total rewrite
   and the private repository's git history would be worthless. Split by
   entity, a corrected room description is a three-line diff.
3. **Lazy loading.** The engine loads the scene it needs, not the book.

### Visibility is part of the schema

Every piece of content carries an explicit visibility marking. Text that may
be read to the table (the boxed read-aloud text of published adventures) is
structurally distinct from notes only the dungeon master may know:

```jsonc
{
  "id": "02-the-cellar",
  "read_aloud": "Die Treppe endet in feuchter Dunkelheit …",
  "gm_notes": "Hinter dem Regal an der Westwand …",
  "assets": [
    { "id": "map-cellar-players", "visibility": "players" },
    { "id": "map-cellar-full",    "visibility": "gm" }
  ]
}
```

This is not an extra burden on ingest: published adventures already make the
distinction typographically, so the pipeline preserves a structure that is
present in the source rather than inventing one.

### The engine reaches content through a port, never through a path

The engine depends on an interface, not on the filesystem:

```python
class AdventureRepository(Protocol):
    def manifest(self) -> AdventureManifest: ...
    def scene(self, scene_id: SceneId) -> Scene: ...
    def npc(self, npc_id: NpcId) -> Npc: ...
    def asset(self, asset_id: AssetId) -> BinaryIO: ...
```

`FileSystemAdventureRepository` reads a package directory; the path comes
from configuration. Tests use an in-memory implementation with original or
SRD 5.1/5.2 content. Because no engine module knows a content path, the
"no content in the repository" rule is structural rather than aspirational.

### Assets are served through the backend, never as static files

The package directory is never exposed to the web client. An asset reaches
the table only via a backend endpoint that checks the current reveal state.
A map the party has not found must not be fetchable by guessing a URL —
otherwise the hidden information guaranteed by ADR-0002 leaks through the
asset path.

### The schema is versioned and validated at both ends

`schema_version` sits in the manifest. JSON Schema definitions live in this
repository under `schemas/adventure/v1/`. The ingest pipeline validates what
it writes; the loader validates what it reads. The public repository also
publishes the validator as a command, so the private repository can run it
in its own CI — the engine's contract is checked against the content without
either repository seeing the other's concerns.

## Consequences

What becomes easy:

- Adventures are versioned, diffable and backed up, without the engine ever
  depending on where they live.
- A second adventure, or a hand-written test adventure, is just another
  package. Nothing in the engine changes.
- Adding images later is an asset entry and a visibility flag, not a format
  redesign.
- Revealing information becomes a state transition over declared visibility,
  rather than a judgement the agent has to be trusted with each time.

What becomes hard, and what we accept:

- Two repositories, and a configured path to connect them. Setup gains a
  step, and a missing or stale content checkout is a new failure mode the
  loader must report clearly.
- The private repository will contain literal copies of copyrighted artwork.
  Scanned images are a straight copy in a way that restructured text is not,
  so the repository must stay private without exception, and no export,
  backup or debug dump may embed assets.
- Schema evolution now costs something: a change touches the pipeline, the
  schema, the loader, and every existing package.

Watch for: pipeline tests are the likeliest place for scanned material to
enter this repository by accident. Their fixtures must be original or SRD
content, and a check in CI should enforce that assumption.

Revisit this decision if: the private repository grows large enough with
image assets that Git LFS becomes necessary, or if a second person ever
needs to run the application, at which point distributing a package becomes
a real question.

## Follow-up

- Define the v1 adventure schema. This is iteration work, not ADR work.
- Decide where the ingest pipeline's own intermediate artefacts (raw OCR
  output) live — almost certainly the private repository, or nowhere.
- ADR-0004: character state ownership (proposed).
