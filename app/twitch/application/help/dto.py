from dataclasses import dataclass
from typing import Set

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class HelpDTO(ChatContextDTO):
    command_prefix: str
    commands: Set[str]
