from dataclasses import dataclass
from typing import Set

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class HelpDTO(ChatContextDTO):
    command_prefix: str
    commands: Set[str]
