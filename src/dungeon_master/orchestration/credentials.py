"""Which credential the Claude Code CLI runs on, and proof that it does (ADR-0007).

The CLI picks its credential itself, in this order: `ANTHROPIC_AUTH_TOKEN`,
`ANTHROPIC_API_KEY`, an API key helper, `CLAUDE_CODE_OAUTH_TOKEN`, and last
the login `claude /login` stored. The Agent SDK hands the CLI the backend's
whole environment with `ClaudeAgentOptions.env` on top, so a variable cannot be
removed, only overridden. An empty value is how one is switched off.

The application never reads, stores or passes on a subscription credential:
in subscription mode it only makes sure nothing outranks the maintainer's own
login. API key helpers come from settings files, which the adapter does not
load (`setting_sources=[]`).
"""

from ..settings import CredentialMode, Settings

# The variables that outrank the subscription login in the CLI's order.
OUTRANKING_SUBSCRIPTION = ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")

# What the CLI's init message reports as `apiKeySource` for each mode, measured
# against the CLI bundled with claude-agent-sdk 0.2.163 (CLI 2.1.286) on
# 2026-10-03: "none" when it runs on the claude.ai login — also with an API key
# in the backend's environment, once it is overridden empty — and
# "ANTHROPIC_API_KEY" when a key is set. Without the override, an inherited key
# wins and reports the latter.
EXPECTED_SOURCES: dict[CredentialMode, frozenset[str]] = {
    "subscription": frozenset({"none"}),
    "api_key": frozenset({"ANTHROPIC_API_KEY"}),
}

REDACTED = "[redacted]"


class NoApiKey(Exception):
    """api_key mode was asked for, but no key is configured."""


class CredentialSwitch:
    """The active credential mode, switchable between turns."""

    def __init__(self, settings: Settings) -> None:
        self._key = settings.anthropic_api_key
        self._mode: CredentialMode = settings.credential_mode
        if self._mode == "api_key":
            self._require_key()

    @property
    def mode(self) -> CredentialMode:
        """The mode, never the credential: for the journal and the game master view."""
        return self._mode

    @property
    def api_key_configured(self) -> bool:
        return self._key is not None and bool(self._key.get_secret_value())

    def switch(self, mode: CredentialMode) -> None:
        """Takes effect at the next turn."""
        if mode == "api_key":
            self._require_key()
        self._mode = mode

    def cli_environment(self) -> dict[str, str]:
        """What the CLI's environment gets on top of the backend's own."""
        if self._mode == "subscription":
            return {name: "" for name in OUTRANKING_SUBSCRIPTION}
        assert self._key is not None
        return {
            "ANTHROPIC_AUTH_TOKEN": "",  # would outrank the key
            "ANTHROPIC_API_KEY": self._key.get_secret_value(),
        }

    def matches(self, api_key_source: str | None) -> bool:
        return api_key_source in EXPECTED_SOURCES[self._mode]

    def redact(self, text: str) -> str:
        """The text with the configured key, should it be in it, replaced."""
        if self.api_key_configured:
            assert self._key is not None
            text = text.replace(self._key.get_secret_value(), REDACTED)
        return text

    def _require_key(self) -> None:
        if not self.api_key_configured:
            raise NoApiKey("No API key is configured: set DM_ANTHROPIC_API_KEY.")
