from dataclasses import dataclass
from datetime import datetime

from app.bot.domain.model.status import BotStatus


@dataclass(frozen=True)
class Bot:
    channel_name: str
    status: BotStatus
    started_at: datetime
