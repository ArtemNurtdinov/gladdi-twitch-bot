from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class CommandShopDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    command_buy_name: str


@dataclass(frozen=True)
class CommandBuyDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    item_name_input: Optional[str]
    command_prefix: str

