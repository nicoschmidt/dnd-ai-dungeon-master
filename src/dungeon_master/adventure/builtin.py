"""Iteration 001's fight, built in: an SRD opponent and an original premise.

Loaded from `fixtures/iteration-001/`, which is laid out like an adventure
package (ADR-0003) so that the filesystem implementation of 002 reads the same
shape. Its provenance is in `fixtures/PROVENANCE.md`.
"""

import json
from importlib.resources import files

from .models import EncounterSetup, Monster
from .repository import InMemoryAdventureRepository

ITERATION_001 = "iteration-001"


def iteration_001_repository() -> InMemoryAdventureRepository:
    """The built-in content, validated as it loads: a bad fixture fails here, not at the table."""
    package = files(__package__).joinpath("fixtures", ITERATION_001)
    monsters = [
        Monster.model_validate(json.loads(entry.read_text(encoding="utf-8")))
        for entry in sorted(package.joinpath("monsters").iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".json")
    ]
    encounters = [
        EncounterSetup.model_validate(json.loads(entry.read_text(encoding="utf-8")))
        for entry in sorted(package.joinpath("encounters").iterdir(), key=lambda e: e.name)
        if entry.name.endswith(".json")
    ]
    return InMemoryAdventureRepository(monsters, encounters)
