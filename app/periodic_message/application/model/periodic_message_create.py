from dataclasses import dataclass


@dataclass(frozen=True)
class CreatePeriodicMessageDTO:
    channel_name: str
    content: str
    use_llm: bool
    interval_minutes: int
    is_enabled: bool
