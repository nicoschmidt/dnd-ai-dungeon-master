"""What a tool gives back to the model."""

from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Done, with data, or refused, with a reason.

    A refusal is a result rather than an exception, so the model is told why and
    can correct itself instead of narrating something the state does not
    support (docs/domain/combat.md).
    """

    ok: bool
    reason: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def done(cls, **data: Any) -> "ToolResult":
        return cls(ok=True, data=data)

    @classmethod
    def refused(cls, reason: str) -> "ToolResult":
        return cls(ok=False, reason=reason)
