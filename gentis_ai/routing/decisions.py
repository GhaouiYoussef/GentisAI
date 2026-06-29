from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RoutingDecision(BaseModel):
    experts: list[str]
    mode: Literal["single", "hybrid", "fallback"]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = ""

    @field_validator("experts")
    @classmethod
    def _non_empty_experts(cls, value: list[str]) -> list[str]:
        return [name for name in value if name]

    def __iter__(self):
        return iter(self.experts)

    def __len__(self) -> int:
        return len(self.experts)

    def __getitem__(self, index: int) -> str:
        return self.experts[index]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            return self.experts == other
        return super().__eq__(other)
