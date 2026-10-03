"""Which credential reaches the Claude Code CLI (ADR-0007), proven without a model."""

import dataclasses
import json
import stat
from pathlib import Path

import pytest
from claude_agent_sdk import query
from fakes import ScriptedDungeonMaster

from dungeon_master.adventure.builtin import iteration_001_repository
from dungeon_master.orchestration.agent_sdk import AgentSdkDungeonMaster
from dungeon_master.orchestration.credentials import REDACTED, CredentialSwitch, NoApiKey
from dungeon_master.orchestration.session import TableSession
from dungeon_master.settings import Settings

KEY = "sk-ant-configured-test-key"
FOREIGN_KEY = "sk-ant-exported-for-another-project"

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def settings(**overrides) -> Settings:
    return Settings(**overrides)


# The environment the CLI is given on top of the backend's own.


def test_subscription_switches_off_everything_that_outranks_the_login() -> None:
    env = CredentialSwitch(settings(anthropic_api_key=KEY)).cli_environment()

    assert env == {"ANTHROPIC_AUTH_TOKEN": "", "ANTHROPIC_API_KEY": ""}


def test_api_key_mode_passes_the_configured_key_and_nothing_that_outranks_it() -> None:
    switch = CredentialSwitch(settings(credential_mode="api_key", anthropic_api_key=KEY))

    assert switch.cli_environment() == {"ANTHROPIC_AUTH_TOKEN": "", "ANTHROPIC_API_KEY": KEY}


def test_api_key_mode_needs_a_key() -> None:
    with pytest.raises(NoApiKey):
        CredentialSwitch(settings(credential_mode="api_key"))

    switch = CredentialSwitch(settings())
    with pytest.raises(NoApiKey):
        switch.switch("api_key")
    assert switch.mode == "subscription"


def test_the_switch_goes_both_ways() -> None:
    switch = CredentialSwitch(settings(anthropic_api_key=KEY))

    switch.switch("api_key")
    assert switch.cli_environment()["ANTHROPIC_API_KEY"] == KEY
    switch.switch("subscription")
    assert switch.cli_environment()["ANTHROPIC_API_KEY"] == ""


@pytest.mark.parametrize(
    ("mode", "source", "matches"),
    [
        ("subscription", "none", True),
        ("subscription", "ANTHROPIC_API_KEY", False),
        ("api_key", "ANTHROPIC_API_KEY", True),
        ("api_key", "none", False),
        ("api_key", None, False),
    ],
)
def test_the_reported_source_is_checked_against_the_mode(
    mode: str, source: str | None, matches: bool
) -> None:
    switch = CredentialSwitch(settings(anthropic_api_key=KEY))
    switch.switch(mode)  # type: ignore[arg-type]

    assert switch.matches(source) is matches


def test_the_key_never_shows_in_the_settings_repr() -> None:
    assert KEY not in repr(settings(anthropic_api_key=KEY))


def test_redaction_removes_the_configured_key() -> None:
    switch = CredentialSwitch(settings(anthropic_api_key=KEY))

    assert switch.redact(f"failed with {KEY} in it") == f"failed with {REDACTED} in it"


# The real SDK transport, against a stand-in for the CLI that writes down its
# environment and exits. This is the process the key must not reach.

# `env python3` rather than this interpreter's path: a shebang cannot hold the
# spaces a checkout's path may have, and the stand-in needs only the stdlib.
FAKE_CLI = """\
#!/usr/bin/env python3
import json, os, sys
if "-v" in sys.argv or "--version" in sys.argv:
    print("2.1.286 (Claude Code)")
    sys.exit(0)
with open(os.environ["FAKE_CLI_ENV_DUMP"], "w") as dump:
    json.dump(dict(os.environ), dump)
sys.exit(1)
"""


async def environment_of_the_cli(tmp_path: Path, switch: CredentialSwitch) -> dict[str, str]:
    cli = tmp_path / "claude"
    cli.write_text(FAKE_CLI)
    cli.chmod(cli.stat().st_mode | stat.S_IEXEC)
    dump = tmp_path / "env.json"

    adapter = AgentSdkDungeonMaster(
        settings(agent_dir=tmp_path / "agent"), switch, iteration_001_repository()
    )
    table = TableSession(ScriptedDungeonMaster())
    options = adapter.options(table.tools)
    options = dataclasses.replace(
        options, cli_path=cli, env={**options.env, "FAKE_CLI_ENV_DUMP": str(dump)}
    )
    with pytest.raises(Exception):
        async for _ in query(prompt="hello", options=options):
            pass
    return json.loads(dump.read_text())


async def test_a_key_in_the_backends_environment_does_not_reach_the_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FOREIGN_KEY)
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", FOREIGN_KEY)

    env = await environment_of_the_cli(tmp_path, CredentialSwitch(settings(anthropic_api_key=KEY)))

    assert env["ANTHROPIC_API_KEY"] == ""
    assert env["ANTHROPIC_AUTH_TOKEN"] == ""
    assert FOREIGN_KEY not in json.dumps(env)
    assert KEY not in json.dumps(env)


async def test_in_api_key_mode_the_cli_gets_the_configured_key_not_the_exported_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FOREIGN_KEY)
    switch = CredentialSwitch(settings(credential_mode="api_key", anthropic_api_key=KEY))

    env = await environment_of_the_cli(tmp_path, switch)

    assert env["ANTHROPIC_API_KEY"] == KEY
    assert FOREIGN_KEY not in json.dumps(env)


def test_a_copied_env_example_starts_on_the_defaults() -> None:
    example = Path(__file__).resolve().parent.parent / ".env.example"

    loaded = Settings(_env_file=example)

    assert (loaded.credential_mode, loaded.anthropic_api_key) == ("subscription", None)
    assert loaded.model == "claude-opus-5"


def test_the_key_is_read_from_its_own_variable_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FOREIGN_KEY)
    monkeypatch.setenv("DM_ANTHROPIC_API_KEY", KEY)

    assert Settings().anthropic_api_key.get_secret_value() == KEY
