"""The port through which the engine reaches adventure content (ADR-0003).

The engine asks for content by identity and never knows where it is stored.
Iteration 001 needs only an opponent; the manifest, scenes, NPCs and assets
join the port with the v1 adventure schema (#4) and the filesystem
implementation in 002.
"""

from collections.abc import Iterable
from typing import Protocol

from .models import EncounterSetup, Monster


class UnknownContent(LookupError):
    """Asked for content the adventure does not have. The message names it."""


class AdventureRepository(Protocol):
    def monster(self, monster_id: str) -> Monster: ...

    def encounter_setup(self, encounter_id: str) -> EncounterSetup: ...


class InMemoryAdventureRepository:
    """Content held in memory: for tests, and for iteration 001's built-in fight."""

    def __init__(
        self, monsters: Iterable[Monster], encounters: Iterable[EncounterSetup] = ()
    ) -> None:
        self._monsters = {m.id: m for m in monsters}
        self._encounters = {e.id: e for e in encounters}
        for encounter in self._encounters.values():
            if encounter.opponent_id not in self._monsters:
                raise UnknownContent(
                    f"Encounter {encounter.id!r} names opponent {encounter.opponent_id!r}, "
                    f"which this adventure does not have."
                )

    def monster(self, monster_id: str) -> Monster:
        return _lookup(self._monsters, "monster", monster_id)

    def encounter_setup(self, encounter_id: str) -> EncounterSetup:
        return _lookup(self._encounters, "encounter", encounter_id)


def _lookup[T](items: dict[str, T], kind: str, wanted: str) -> T:
    try:
        return items[wanted]
    except KeyError:
        known = ", ".join(sorted(items)) or "none"
        raise UnknownContent(f"No {kind} {wanted!r} in this adventure. Known: {known}.") from None
