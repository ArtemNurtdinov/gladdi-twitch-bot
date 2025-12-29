from dataclasses import dataclass
from datetime import datetime
from typing import Set

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class HelpDTO:
    command_prefix: str
    channel_name: str
    bot_nick: str
    occurred_at: datetime
    commands: Set[str]
