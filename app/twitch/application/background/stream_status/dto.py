from dataclasses import dataclass


@dataclass(frozen=True)
class StreamStatusDTO:
    channel_name: str
