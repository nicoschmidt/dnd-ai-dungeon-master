"""ADR-0005, commitment 4: no web framework or Agent SDK below the API layer.

The rules core, session state, the table's event contract, the tool layer and
the adventure port must import neither a web framework nor the Claude Agent
SDK. Nor may they import the API or orchestration packages, which would bring
either in by the back door. The check reads the source with `ast` rather than
importing it, so it names the file and line of every offending import and is
not fooled by a module that merely mentions one.
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"

GUARDED_PACKAGES = (
    "dungeon_master.rules",
    "dungeon_master.session",
    "dungeon_master.events",
    "dungeon_master.tools",
    "dungeon_master.adventure",
)

FORBIDDEN = (
    "fastapi",
    "starlette",
    "uvicorn",
    "claude_agent_sdk",
    "dungeon_master.api",
    "dungeon_master.orchestration",
)


def _module_name(path: Path, src: Path) -> str:
    parts = list(path.relative_to(src).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imported_names(tree: ast.Module, module: str, is_package: bool):
    """Yield (line, absolute module name) for every import in the tree."""
    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
            else:
                anchor = package.split(".")
                if node.level > 1:
                    anchor = anchor[: -(node.level - 1)]
                base = ".".join(anchor + ([node.module] if node.module else []))
            yield node.lineno, base
            # `from dungeon_master import api` imports a forbidden package too.
            for alias in node.names:
                yield node.lineno, f"{base}.{alias.name}"


def _is_forbidden(name: str) -> bool:
    return any(name == f or name.startswith(f + ".") for f in FORBIDDEN)


def forbidden_imports(src: Path, packages=GUARDED_PACKAGES) -> list[str]:
    """Return one `path:line imports name` entry per offending import."""
    offences = []
    for package in packages:
        for path in sorted((src / package.replace(".", "/")).rglob("*.py")):
            module = _module_name(path, src)
            tree = ast.parse(path.read_text(), filename=str(path))
            seen = set()
            for line, name in _imported_names(tree, module, path.name == "__init__.py"):
                if _is_forbidden(name) and line not in seen:
                    seen.add(line)
                    offences.append(f"{path.relative_to(src.parent)}:{line} imports {name}")
    return offences


def test_layers_below_the_api_import_no_framework_or_sdk() -> None:
    offences = forbidden_imports(SRC)

    assert not offences, (
        "The rules core, session state, events and tools must not import a web "
        "framework or the Agent SDK (ADR-0005, commitment 4):\n  " + "\n  ".join(offences)
    )


@pytest.fixture
def fake_src(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    for package in ("dungeon_master", "dungeon_master/rules", "dungeon_master/session"):
        (src / package).mkdir(parents=True, exist_ok=True)
        (src / package / "__init__.py").write_text("")
    return src


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("import fastapi\n", "1 imports fastapi"),
        ("from starlette.responses import JSONResponse\n", "1 imports starlette.responses"),
        ("import claude_agent_sdk as sdk\n", "1 imports claude_agent_sdk"),
        ("import uvicorn.config\n", "1 imports uvicorn.config"),
        ("from ..api import app\n", "1 imports dungeon_master.api"),
        ("from dungeon_master import orchestration\n", "1 imports dungeon_master.orchestration"),
        ("def f():\n    import fastapi\n", "2 imports fastapi"),
    ],
)
def test_checker_names_the_file_line_and_import(fake_src: Path, source: str, expected: str) -> None:
    (fake_src / "dungeon_master/rules/dice.py").write_text(source)

    offences = forbidden_imports(fake_src)

    assert offences == [f"src/dungeon_master/rules/dice.py:{expected}"]


def test_checker_accepts_the_standard_library_and_sibling_layers(fake_src: Path) -> None:
    (fake_src / "dungeon_master/session/party.py").write_text(
        '"""Mentions fastapi and claude_agent_sdk only in prose."""\n'
        "import random\n"
        "from dataclasses import dataclass\n"
        "from ..rules import dice\n"
        "from dungeon_master.rules.dice import roll\n"
        "from . import state\n"
    )

    assert forbidden_imports(fake_src) == []
