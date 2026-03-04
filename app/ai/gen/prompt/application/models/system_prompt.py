from dataclasses import dataclass


@dataclass(frozen=True)
class SystemPromptDTO:
    channel_name: str
    prompt: str