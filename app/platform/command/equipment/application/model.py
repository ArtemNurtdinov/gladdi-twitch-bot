from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EquipmentDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_name: str
    occurred_at: datetime
    message: str
    command_prefix: str
    command_shop: str
