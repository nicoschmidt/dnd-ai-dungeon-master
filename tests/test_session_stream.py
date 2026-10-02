"""The table's stream and the declared action, against a scripted dungeon master.

No model is called. A test declares an action, waits for the turn to finish,
closes the session's event log so the stream ends, and reads what a browser
would have received.
"""

import asyncio
import json
from pathlib import Path

import pytest
from fastapi import FastAPI

from fakes import Call, Fail, Hold, Say, ScriptedDungeonMaster
from table_client import client as _client
from table_client import frames as _frames

from dungeon_master.api.app import create_app
from dungeon_master.events.contract import NarrationDelta, TableError
from dungeon_master.events.log import EventLog
from dungeon_master.orchestration.session import TableSession
from dungeon_master.orchestration.stand_in import StandInDungeonMaster
from dungeon_master.session.party import Character

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _app(tmp_path: Path, dungeon_master) -> FastAPI:
    return create_app(tmp_path / "no-build", dungeon_master)


def _table(app: FastAPI) -> TableSession:
    return app.state.session


async def _declare_and_read(app: FastAPI, text: str, last_event_id: str | None = None):
    async with _client(app) as client:
        response = await client.post("/api/session/actions", json={"text": text})
        assert response.status_code == 202
        await _table(app).turns.wait()
        _table(app).events.close()
        headers = {"Last-Event-ID": last_event_id} if last_event_id else {}
        stream = await client.get("/api/session/stream", headers=headers)
    return response, stream


def _add_brann(app: FastAPI) -> None:
    _table(app).state.party.append(
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


async def test_a_turn_reaches_the_table_as_named_events_in_order(tmp_path: Path) -> None:
    app = _app(
        tmp_path,
        ScriptedDungeonMaster(
            Say("Der Oger "),
            Say("taumelt "),
            Call("add_condition", {"target": "brann", "condition": "prone"}),
            Say("und fällt."),
        ),
    )
    _add_brann(app)

    accepted, stream = await _declare_and_read(app, "I trip him, 17")

    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    frames = _frames(stream.text)
    assert [f["event"] for f in frames] == [
        "turn_started",
        "narration_delta",
        "narration_delta",
        "party_updated",
        "narration_delta",
        "turn_finished",
    ]
    payloads = [json.loads(f["data"]) for f in frames]
    turn_id = accepted.json()["turn_id"]
    assert payloads[0]["action"] == {"text": "I trip him, 17", "character_id": None}
    assert [p["text"] for p in payloads if p["type"] == "narration_delta"] == [
        "Der Oger ",
        "taumelt ",
        "und fällt.",
    ]
    assert payloads[3]["party"][0]["conditions"] == ["prone"]
    assert all(p.get("turn_id", turn_id) == turn_id for p in payloads)


async def test_every_frame_carries_its_type_in_the_event_name_and_the_payload(
    tmp_path: Path,
) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Say("Ja.")))

    _, stream = await _declare_and_read(app, "Hallo")

    for frame in _frames(stream.text):
        assert json.loads(frame["data"])["type"] == frame["event"]


async def test_event_ids_are_sequential_within_the_session(tmp_path: Path) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Say("a"), Say("b")))

    _, stream = await _declare_and_read(app, "x")

    session_id = _table(app).events.session_id
    assert [f["id"] for f in _frames(stream.text)] == [f"{session_id}:{n}" for n in range(1, 5)]


async def test_a_reconnecting_client_receives_only_what_it_missed(tmp_path: Path) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Say("a"), Say("b"), Say("c")))
    session_id = _table(app).events.session_id

    _, stream = await _declare_and_read(app, "x", last_event_id=f"{session_id}:2")

    frames = _frames(stream.text)
    assert [f["id"] for f in frames] == [f"{session_id}:{n}" for n in (3, 4, 5)]
    assert [json.loads(f["data"]).get("text") for f in frames] == ["b", "c", None]


async def test_a_client_from_before_a_restart_receives_the_whole_session(tmp_path: Path) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Say("a")))

    _, stream = await _declare_and_read(app, "x", last_event_id="an-earlier-process:57")

    assert [f["event"] for f in _frames(stream.text)] == [
        "turn_started",
        "narration_delta",
        "turn_finished",
    ]


async def test_an_action_during_a_turn_is_refused(tmp_path: Path) -> None:
    release = asyncio.Event()
    app = _app(tmp_path, ScriptedDungeonMaster(Hold(release), Say("fertig")))

    async with _client(app) as client:
        first = await client.post("/api/session/actions", json={"text": "erste"})
        second = await client.post("/api/session/actions", json={"text": "zweite"})
        release.set()
        await _table(app).turns.wait()
        third = await client.post("/api/session/actions", json={"text": "dritte"})
        await _table(app).turns.wait()

    assert [r.status_code for r in (first, second, third)] == [202, 409, 202]


async def test_an_empty_action_is_rejected(tmp_path: Path) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster())

    async with _client(app) as client:
        response = await client.post("/api/session/actions", json={"text": ""})

    assert response.status_code == 422


async def test_a_failing_dungeon_master_is_an_error_event_without_its_message(
    tmp_path: Path,
) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Say("Der "), Fail("sk-ant-secret in a traceback")))

    _, stream = await _declare_and_read(app, "x")

    frames = _frames(stream.text)
    assert [f["event"] for f in frames] == [
        "turn_started",
        "narration_delta",
        "error",
        "turn_finished",
    ]
    error = TableError.model_validate_json(frames[2]["data"])
    assert error.code == "agent_failed"
    assert "secret" not in stream.text


async def test_a_turn_can_follow_a_failed_one(tmp_path: Path) -> None:
    app = _app(tmp_path, ScriptedDungeonMaster(Fail()))

    async with _client(app) as client:
        first = await client.post("/api/session/actions", json={"text": "x"})
        await _table(app).turns.wait()
        second = await client.post("/api/session/actions", json={"text": "y"})
        await _table(app).turns.wait()

    assert [first.status_code, second.status_code] == [202, 202]


async def test_the_stand_in_answers_word_by_word(tmp_path: Path) -> None:
    app = _app(tmp_path, StandInDungeonMaster(delay=0))

    _, stream = await _declare_and_read(app, "I attack, 17")

    deltas = [json.loads(f["data"])["text"] for f in _frames(stream.text) if f["event"] == "narration_delta"]
    assert len(deltas) > 1
    assert "".join(deltas).endswith("You declared: I attack, 17")


async def test_a_live_subscriber_receives_events_as_they_are_published() -> None:
    log = EventLog(session_id="s")
    received = []

    async def follow() -> None:
        async for event_id, event in log.subscribe():
            received.append((event_id, event.text))

    follower = asyncio.create_task(follow())
    await asyncio.sleep(0)
    log.publish(NarrationDelta(turn_id="t", text="a"))
    await asyncio.sleep(0)
    log.publish(NarrationDelta(turn_id="t", text="b"))
    log.close()
    await asyncio.wait_for(follower, timeout=1)

    assert received == [("s:1", "a"), ("s:2", "b")]
