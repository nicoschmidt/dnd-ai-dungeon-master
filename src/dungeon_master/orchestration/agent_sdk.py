"""The dungeon master as a Claude agent, through the Claude Agent SDK.

The only module that imports `claude_agent_sdk` (ADR-0005, commitment 4). It
implements the `DungeonMaster` port: one `query()` per declared action,
resuming the same agent session each time, so the credential environment is
built afresh for every turn and a switch of mode takes effect at the next one
(ADR-0007).

The agent gets no built-in tools — no shell, no files — and none of the
maintainer's Claude Code settings or CLAUDE.md: only the tool surface of
`dungeon_master.tools`, run in this process.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import aclosing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    RateLimitEvent,
    ResultError,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    create_sdk_mcp_server,
    tool,
)
from claude_agent_sdk import query as sdk_query

from ..adventure.builtin import ITERATION_001
from ..adventure.repository import AdventureRepository
from ..events.contract import DeclaredAction
from ..settings import CredentialMode, Settings
from ..tools.registry import ToolSpec
from ..tools.toolbox import ToolBox
from .agent import DungeonMasterError
from .credentials import CredentialSwitch
from .prompt import system_prompt, turn_prompt

SERVER = "dm"
MAX_AGENT_TURNS_PER_ACTION = 30
"""A bound on model round trips while answering one declared action."""


@dataclass(frozen=True)
class TurnRecord:
    """What one model turn cost and ran on — for the journal (#33). Never a credential.

    `total_cost_usd` is as the SDK reports it, which for a resumed session was
    measured to be cumulative over the session, not per turn.
    """

    session_id: str
    credential_mode: CredentialMode
    model: str
    total_cost_usd: float | None
    usage: dict[str, Any] | None
    model_usage: dict[str, Any] | None
    duration_ms: int
    is_error: bool


class AgentSdkDungeonMaster:
    def __init__(
        self,
        settings: Settings,
        credentials: CredentialSwitch,
        adventure: AdventureRepository,
        *,
        encounter_id: str = ITERATION_001,
        query: Callable[..., AsyncIterator[Any]] = sdk_query,
    ) -> None:
        setup = adventure.encounter_setup(encounter_id)
        self._system_prompt = system_prompt(
            settings.narration_language, setup, adventure.monster(setup.opponent_id)
        )
        self._model = settings.model
        self._agent_dir = settings.agent_dir
        self._credentials = credentials
        self._query = query
        self.session_id: str | None = None
        self.last_turn: TurnRecord | None = None

    def options(self, tools: ToolBox) -> ClaudeAgentOptions:
        server = create_sdk_mcp_server(
            name=SERVER, tools=[_sdk_tool(spec, tools) for spec in tools.specs]
        )
        self._agent_dir.mkdir(parents=True, exist_ok=True)
        return ClaudeAgentOptions(
            system_prompt=self._system_prompt,
            model=self._model,
            tools=[],
            mcp_servers={SERVER: server},
            allowed_tools=[f"mcp__{SERVER}__{spec.name}" for spec in tools.specs],
            setting_sources=[],
            include_partial_messages=True,
            env=self._credentials.cli_environment(),
            max_turns=MAX_AGENT_TURNS_PER_ACTION,
            resume=self.session_id,
            cwd=self._agent_dir,
        )

    async def take_turn(self, action: DeclaredAction, tools: ToolBox) -> AsyncIterator[str]:
        mode = self._credentials.mode
        options = self.options(tools)
        prompt = turn_prompt(action, tools.party(), tools.encounter())
        narrated = False
        try:
            async with aclosing(self._query(prompt=prompt, options=options)) as messages:
                async for message in messages:
                    match message:
                        case SystemMessage(subtype="init", data=data):
                            self._check_credential(mode, data.get("apiKeySource"))
                            self.session_id = data.get("session_id") or self.session_id
                        case StreamEvent(event=event, parent_tool_use_id=None):
                            # Text before and after a tool call arrives as separate
                            # blocks; the table reads them as paragraphs.
                            if narrated and _starts_text_block(event):
                                yield "\n\n"
                            if text := _narration(event):
                                narrated = True
                                yield text
                        case RateLimitEvent(rate_limit_info=info) if info.status == "rejected":
                            raise _limit_reached(mode)
                        case AssistantMessage(error=error) if error:
                            raise _assistant_error(mode, error)
                        case ResultMessage():
                            self._record(mode, message)
        except ResultError as error:
            if error.api_error_status == 429:
                raise _limit_reached(mode) from None
            if error.api_error_status in (401, 403):
                raise _assistant_error(mode, "authentication_failed") from None
            raise

    def _check_credential(self, mode: CredentialMode, source: str | None) -> None:
        if not self._credentials.matches(source):
            raise DungeonMasterError(
                "credential_mismatch",
                f"The dungeon master would have run on {source!r} instead of the chosen "
                f"{mode} mode, so it was stopped before anything reached the model.",
            )

    def _record(self, mode: CredentialMode, result: ResultMessage) -> None:
        self.session_id = result.session_id
        self.last_turn = TurnRecord(
            session_id=result.session_id,
            credential_mode=mode,
            model=self._model,
            total_cost_usd=result.total_cost_usd,
            usage=result.usage,
            model_usage=result.model_usage,
            duration_ms=result.duration_ms,
            is_error=result.is_error,
        )


def _sdk_tool(spec: ToolSpec, tools: ToolBox):
    """One of our tools, as the agent sees it. A refusal is a result, not an error."""

    @tool(spec.name, spec.description, spec.arguments.model_json_schema())
    async def run(args: dict[str, Any]) -> dict[str, Any]:
        result = tools.call(spec.name, args)
        return {"content": [{"type": "text", "text": result.model_dump_json()}]}

    return run


def _starts_text_block(event: dict[str, Any]) -> bool:
    block = event.get("content_block") or {}
    return event.get("type") == "content_block_start" and block.get("type") == "text"


def _narration(event: dict[str, Any]) -> str | None:
    """The text of a streamed text delta; thinking and tool input are not narration."""
    if event.get("type") != "content_block_delta":
        return None
    delta = event.get("delta") or {}
    return delta.get("text") if delta.get("type") == "text_delta" else None


SWITCH_HINT = 'PUT /api/session/credentials with {"mode": "api_key"}'


def _limit_reached(mode: CredentialMode) -> DungeonMasterError:
    if mode == "subscription":
        return DungeonMasterError(
            "usage_limit_reached",
            "The Claude subscription's usage limit is reached. Switch the dungeon master "
            f"to the API key ({SWITCH_HINT}) and declare the action again.",
        )
    return DungeonMasterError(
        "usage_limit_reached",
        "The API key's rate limit is reached. Wait a moment, then declare the action again.",
    )


def _assistant_error(mode: CredentialMode, error: str) -> Exception:
    if error == "rate_limit":
        return _limit_reached(mode)
    if error == "authentication_failed":
        return DungeonMasterError(
            "authentication_failed",
            "Claude Code is not logged in on this machine: run `claude /login` or "
            "`claude setup-token`, then declare the action again."
            if mode == "subscription"
            else "The API key was rejected. Check DM_ANTHROPIC_API_KEY.",
        )
    return RuntimeError(f"the model call failed: {error}")
