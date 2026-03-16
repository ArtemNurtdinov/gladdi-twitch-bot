from dataclasses import dataclass


@dataclass(frozen=True)
class IntentDetectorConfig:
    host: str
