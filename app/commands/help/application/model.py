from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HelpDTO:
    command_prefix: str
    channel_name: str
    bot_nick: str
    occurred_at: datetime
    commands: set[str]
