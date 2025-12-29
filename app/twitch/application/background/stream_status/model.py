from dataclasses import dataclass


@dataclass(frozen=True)
class StatusJobDTO:
    channel_name: str
