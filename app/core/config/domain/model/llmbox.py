from dataclasses import dataclass


@dataclass(frozen=True)
class LLMBoxConfig:
    host: str
