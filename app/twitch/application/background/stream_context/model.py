from dataclasses import dataclass


@dataclass(frozen=True)
class RestoreStreamJobDTO:
    channel_name: str