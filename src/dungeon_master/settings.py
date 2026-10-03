"""The backend's configuration: environment variables prefixed `DM_`, or `.env`.

`.env` sits in the repository root and is never committed (`.gitignore`);
`.env.example` names every variable without a value. Credentials are typed as
`SecretStr`, so they never appear in a repr, a log line or an error message
by accident (ADR-0007).
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

CredentialMode = Literal["subscription", "api_key"]


class Settings(BaseSettings):
    # Empty values mean "the default", so a copied .env.example works unchanged.
    model_config = SettingsConfigDict(
        env_prefix="DM_", env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    credential_mode: CredentialMode = Field(
        default="subscription",
        description="What pays for the model: the maintainer's own Claude login, or an API key.",
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description=(
            "A Claude Console API key, used only in api_key mode. Its own variable, so an "
            "ANTHROPIC_API_KEY exported for some other project never counts by accident."
        ),
    )
    model: str = "claude-opus-5"
    narration_language: str = "German"
    dungeon_master: Literal["agent", "stand_in"] = Field(
        default="agent",
        description="`stand_in` answers without a model: for development without credentials.",
    )
    client_dist: Path = Path("client") / "dist"
    agent_dir: Path = Field(
        default=Path.home() / ".dungeon-master" / "agent",
        description=(
            "The agent's working directory, outside the repository. Claude Code keeps the "
            "session transcripts it resumes from under a key derived from it."
        ),
    )
