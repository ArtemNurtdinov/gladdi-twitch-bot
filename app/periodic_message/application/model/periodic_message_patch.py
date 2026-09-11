from dataclasses import dataclass


@dataclass(frozen=True)
class PatchPeriodicMessageDTO:
    id: int
    content: str | None
    use_llm: bool | None
    interval_minutes: int | None
    is_enabled: bool | None
