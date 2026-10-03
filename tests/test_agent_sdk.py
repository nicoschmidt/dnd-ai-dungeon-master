"""The Claude agent behind the DungeonMaster port, against a scripted `query`.

No model, no CLI: `query` is replaced by a function that records the options
it was given and yields real SDK message types.
"""

import json
import logging
from pathlib import Path

import pytest
from claude_agent_sdk import (
    AssistantMessage,
    RateLimitEvent,
    RateLimitInfo,
    ResultError,
    ResultMessage,
    StreamEvent,
    SystemMessage,
)
from table_client import client, frames

from dungeon_master.adventure.builtin import iteration_001_repository
from dungeon_master.api.app import create_app
from dungeon_master.events.contract import PartyUpdated
from dungeon_master.orchestration.agent_sdk import AgentSdkDungeonMaster, _sdk_tool
from dungeon_master.orchestration.credentials import CredentialSwitch
from dungeon_master.session.party import Character
from dungeon_master.settings import Settings

KEY = "sk-ant-configured-test-key"

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def init(source: str = "none", session: str = "session-1") -> SystemMessage:
    return SystemMessage(subtype="init", data={"apiKeySource": source, "session_id": session})


def delta(text: str, parent: str | None = None) -> StreamEvent:
    return StreamEvent(
        uuid="u",
        session_id="session-1",
        event={"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": text}},
        parent_tool_use_id=parent,
    )


def result(session: str = "session-1") -> ResultMessage:
    return ResultMessage(
        subtype="success",
        duration_ms=1200,
        duration_api_ms=1100,
        is_error=False,
        num_turns=1,
        session_id=session,
        total_cost_usd=0.0123,
        usage={"input_tokens": 900, "output_tokens": 120},
    )


class ScriptedQuery:
    """Stands in for `claude_agent_sdk.query`: one script per call."""

    def __init__(self, *scripts: list) -> None:
        self.scripts = list(scripts)
        self.calls: list[dict] = []

    async def __call__(self, *, prompt, options):
        self.calls.append({"prompt": prompt, "options": options})
        for item in self.scripts.pop(0):
            if isinstance(item, BaseException):
                raise item
            yield item


def settings(**overrides) -> Settings:
    return Settings(**overrides)


def app_with(tmp_path: Path, query: ScriptedQuery, **overrides):
    config = settings(agent_dir=tmp_path / "agent", **overrides)
    credentials = CredentialSwitch(config)
    adventure = iteration_001_repository()
    dungeon_master = AgentSdkDungeonMaster(config, credentials, adventure, query=query)
    app = create_app(
        tmp_path / "no-build", dungeon_master, adventure, settings=config, credentials=credentials
    )
    app.state.session.state.party.append(
        Character(
            id="brann",
            name="Brann",
            character_class="Fighter",
            level=3,
            armour_class=16,
            max_hit_points=28,
            current_hit_points=28,
        )
    )
    return app, dungeon_master


async def play(app, *texts: str) -> list[dict]:
    """Declare actions one after another; return the table's events as parsed frames."""
    table = app.state.session
    async with client(app) as http:
        for text in texts:
            response = await http.post("/api/session/actions", json={"text": text})
            assert response.status_code == 202
            await table.turns.wait()
        table.events.close()
        stream = await http.get("/api/session/stream")
    return [json.loads(f["data"]) for f in frames(stream.text)]


# Narration.


async def test_text_deltas_reach_the_table_as_narration(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), delta("Der Oger "), delta("brüllt."), result()])
    app, _ = app_with(tmp_path, query)

    events = await play(app, "Wir nähern uns der Brücke.")

    assert [e["text"] for e in events if e["type"] == "narration_delta"] == ["Der Oger ", "brüllt."]
    assert events[-1]["type"] == "turn_finished"


def block_start(kind: str = "text") -> StreamEvent:
    return StreamEvent(
        uuid="u",
        session_id="session-1",
        event={"type": "content_block_start", "index": 1, "content_block": {"type": kind}},
    )


async def test_text_blocks_around_a_tool_call_become_paragraphs(tmp_path: Path) -> None:
    query = ScriptedQuery(
        [
            init(),
            block_start(),
            delta("Er hebt die Keule."),
            block_start("tool_use"),
            block_start(),
            delta("Würfelt Initiative!"),
            result(),
        ]
    )
    app, _ = app_with(tmp_path, query)

    events = await play(app, "x")

    narration = "".join(e["text"] for e in events if e["type"] == "narration_delta")
    assert narration == "Er hebt die Keule.\n\nWürfelt Initiative!"


async def test_text_inside_a_subagent_is_not_narration(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), delta("hidden", parent="tool-1"), delta("shown"), result()])
    app, _ = app_with(tmp_path, query)

    events = await play(app, "x")

    assert [e["text"] for e in events if e["type"] == "narration_delta"] == ["shown"]


# How the agent is run.


async def test_the_agent_gets_only_the_tool_surface_and_none_of_the_maintainers_settings(
    tmp_path: Path,
) -> None:
    query = ScriptedQuery([init(), result()])
    app, _ = app_with(tmp_path, query, model="claude-sonnet-5")

    await play(app, "x")

    options = query.calls[0]["options"]
    assert options.tools == []
    assert options.setting_sources == []
    assert options.include_partial_messages is True
    assert options.model == "claude-sonnet-5"
    assert set(options.mcp_servers) == {"dm"}
    assert "mcp__dm__opponent_attack" in options.allowed_tools
    assert len(options.allowed_tools) == 13
    assert options.env == {"ANTHROPIC_AUTH_TOKEN": "", "ANTHROPIC_API_KEY": ""}
    assert Path(options.cwd) == tmp_path / "agent"


async def test_the_premise_and_the_language_are_in_the_system_prompt(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), result()])
    app, _ = app_with(tmp_path, query, narration_language="German")

    await play(app, "x")

    prompt = query.calls[0]["options"].system_prompt
    assert "Narrate in German" in prompt
    assert iteration_001_repository().encounter_setup("iteration-001").premise in prompt
    assert 'opponent_id "ogre"' in prompt


async def test_each_turn_names_the_actor_and_the_public_state(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), result()])
    app, _ = app_with(tmp_path, query)

    async with client(app) as http:
        await http.post(
            "/api/session/actions", json={"text": "I attack, 17", "character_id": "brann"}
        )
        await app.state.session.turns.wait()

    prompt = query.calls[0]["prompt"]
    assert prompt.startswith("Brann declares: I attack, 17")
    assert "Brann (id brann), Fighter 3: 28/28 HP" in prompt


async def test_the_next_turn_resumes_the_same_agent_session(tmp_path: Path) -> None:
    query = ScriptedQuery(
        [init(session="session-1"), result(session="session-1")],
        [init(session="session-1"), result(session="session-1")],
    )
    app, dungeon_master = app_with(tmp_path, query)

    await play(app, "first", "second")

    assert query.calls[0]["options"].resume is None
    assert query.calls[1]["options"].resume == "session-1"
    assert dungeon_master.last_turn.total_cost_usd == 0.0123
    assert dungeon_master.last_turn.credential_mode == "subscription"


async def test_a_switch_takes_effect_at_the_next_turn(tmp_path: Path) -> None:
    query = ScriptedQuery(
        [init(), result()],
        [init(source="ANTHROPIC_API_KEY"), result()],
    )
    app, _ = app_with(tmp_path, query, anthropic_api_key=KEY)

    table = app.state.session
    async with client(app) as http:
        await http.post("/api/session/actions", json={"text": "first"})
        await table.turns.wait()
        switched = await http.put("/api/session/credentials", json={"mode": "api_key"})
        await http.post("/api/session/actions", json={"text": "second"})
        await table.turns.wait()
        table.events.close()
        stream = await http.get("/api/session/stream")
    events = [json.loads(f["data"]) for f in frames(stream.text)]

    assert switched.json() == {"mode": "api_key", "api_key_configured": True}
    assert query.calls[1]["options"].env["ANTHROPIC_API_KEY"] == KEY
    assert query.calls[1]["options"].resume == "session-1"
    assert not [e for e in events if e["type"] == "error"]


# The tools, as the agent calls them.


async def test_a_tool_called_by_the_agent_changes_state_and_tells_the_table(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), result()])
    app, _ = app_with(tmp_path, query)
    table = app.state.session
    tool = next(
        _sdk_tool(spec, table.tools) for spec in table.tools.specs if spec.name == "add_condition"
    )

    answer = await tool.handler({"target": "brann", "condition": "prone"})

    assert json.loads(answer["content"][0]["text"])["ok"] is True
    assert table.state.party[0].conditions == ["prone"]
    table.events.close()
    published = [event async for _, event in table.events.subscribe()]
    assert isinstance(published[-1], PartyUpdated)


async def test_a_refusal_goes_back_to_the_agent_as_a_result(tmp_path: Path) -> None:
    query = ScriptedQuery([init(), result()])
    app, _ = app_with(tmp_path, query)
    table = app.state.session
    tool = next(_sdk_tool(spec, table.tools) for spec in table.tools.specs if spec.name == "end_turn")

    answer = await tool.handler({})

    assert answer.get("is_error") is None
    assert json.loads(answer["content"][0]["text"]) == {
        "ok": False,
        "reason": "No encounter has started.",
        "data": {},
    }


# Credentials, limits and failures.


async def test_a_credential_other_than_the_chosen_one_stops_the_turn(tmp_path: Path) -> None:
    query = ScriptedQuery([init(source="ANTHROPIC_API_KEY"), delta("never shown"), result()])
    app, _ = app_with(tmp_path, query)

    events = await play(app, "x")

    errors = [e for e in events if e["type"] == "error"]
    assert [e["code"] for e in errors] == ["credential_mismatch"]
    assert not [e for e in events if e["type"] == "narration_delta"]


@pytest.mark.parametrize(
    "limit",
    [
        RateLimitEvent(
            rate_limit_info=RateLimitInfo(status="rejected"), uuid="u", session_id="session-1"
        ),
        AssistantMessage(content=[], model="claude-opus-5", error="rate_limit"),
        ResultError("limit", data={"api_error_status": 429}),
    ],
    ids=["rate limit event", "assistant error", "result error"],
)
async def test_a_reached_subscription_limit_names_the_switch(tmp_path: Path, limit) -> None:
    query = ScriptedQuery([init(), limit])
    app, _ = app_with(tmp_path, query)

    events = await play(app, "x")

    [error] = [e for e in events if e["type"] == "error"]
    assert error["code"] == "usage_limit_reached"
    assert "/api/session/credentials" in error["message"]


async def test_a_missing_login_says_how_to_log_in(tmp_path: Path) -> None:
    query = ScriptedQuery(
        [init(), AssistantMessage(content=[], model="claude-opus-5", error="authentication_failed")]
    )
    app, _ = app_with(tmp_path, query)

    events = await play(app, "x")

    [error] = [e for e in events if e["type"] == "error"]
    assert error["code"] == "authentication_failed"
    assert "claude /login" in error["message"]


async def test_a_failure_carrying_the_key_reaches_neither_the_table_nor_the_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    query = ScriptedQuery([init(source="ANTHROPIC_API_KEY"), RuntimeError(f"boom with {KEY}")])
    app, _ = app_with(tmp_path, query, credential_mode="api_key", anthropic_api_key=KEY)

    with caplog.at_level(logging.DEBUG):
        events = await play(app, "x")

    assert [e["code"] for e in events if e["type"] == "error"] == ["agent_failed"]
    assert KEY not in json.dumps(events)
    assert "boom with" in caplog.text
    assert KEY not in caplog.text


# The credentials endpoints.


async def test_the_endpoints_show_the_mode_and_never_the_key(tmp_path: Path) -> None:
    app, _ = app_with(tmp_path, ScriptedQuery(), anthropic_api_key=KEY)

    async with client(app) as http:
        before = await http.get("/api/session/credentials")
        switched = await http.put("/api/session/credentials", json={"mode": "api_key"})

    assert before.json() == {"mode": "subscription", "api_key_configured": True}
    assert switched.json()["mode"] == "api_key"
    assert KEY not in before.text + switched.text


async def test_switching_to_a_key_that_is_not_there_is_refused(tmp_path: Path) -> None:
    app, _ = app_with(tmp_path, ScriptedQuery())

    async with client(app) as http:
        response = await http.put("/api/session/credentials", json={"mode": "api_key"})
        after = await http.get("/api/session/credentials")

    assert response.status_code == 422
    assert after.json()["mode"] == "subscription"


def test_without_injection_the_api_and_the_agent_share_one_switch(tmp_path: Path) -> None:
    app = create_app(tmp_path / "no-build", settings=settings(agent_dir=tmp_path / "agent"))

    dungeon_master = app.state.session.turns._dungeon_master
    assert isinstance(dungeon_master, AgentSdkDungeonMaster)
    assert dungeon_master._credentials is app.state.credentials
