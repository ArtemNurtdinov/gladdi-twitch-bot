from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StreamInfoDTO:
    game_name: Optional[str]
    title: Optional[str]
