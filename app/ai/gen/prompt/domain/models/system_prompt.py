from dataclasses import dataclass


@dataclass(frozen=True)
class SystemPrompt:
    channel_name: str
    prompt: str
