"""Export the table's contract as JSON Schema, for the client's generated types.

    python -m dungeon_master.events.schema [output path]

Writes `client/src/contract/table-events.schema.json` by default. The client
turns it into TypeScript with `npm run contract`. Both files are committed;
tests/test_event_contract.py fails when the schema is stale, and CI fails when
the TypeScript is.
"""

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from .contract import CONTRACT_VERSION, DeclaredAction, TableEvent

DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[3] / "client" / "src" / "contract" / "table-events.schema.json"
)


def contract_schema() -> dict:
    """The contract as one JSON Schema document.

    Serialisation mode throughout: a field with a default is always present on
    the wire, so the TypeScript types must not mark it optional.
    """
    refs, schema = TypeAdapter.json_schemas(
        [
            ("event", "serialization", TypeAdapter(TableEvent)),
            ("action", "serialization", TypeAdapter(DeclaredAction)),
        ],
        ref_template="#/$defs/{model}",
    )
    defs = schema["$defs"]
    defs["TableEvent"] = {"title": "TableEvent", **refs[("event", "serialization")]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TableContract",
        "description": (
            f"The table's event contract, version {CONTRACT_VERSION}. Generated from "
            "dungeon_master.events.contract by `python -m dungeon_master.events.schema`; "
            "do not edit by hand."
        ),
        "type": "object",
        "properties": {
            "contract_version": {"const": CONTRACT_VERSION},
            "event": {"$ref": "#/$defs/TableEvent"},
            "action": refs[("action", "serialization")],
        },
        "required": ["contract_version", "event", "action"],
        "additionalProperties": False,
        "$defs": dict(sorted(defs.items())),
    }


def render() -> str:
    return json.dumps(contract_schema(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> None:
    output = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render())
    print(f"wrote {output}")


if __name__ == "__main__":
    main(sys.argv)
