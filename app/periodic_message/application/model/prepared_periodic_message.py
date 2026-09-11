from dataclasses import dataclass


@dataclass(frozen=True)
class PreparedPeriodicMessage:
    message_id: int
    text: str
    interval_minutes: int
    use_llm: bool
    prompt: str
