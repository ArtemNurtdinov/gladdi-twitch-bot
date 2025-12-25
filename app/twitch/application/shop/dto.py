from dataclasses import dataclass
from typing import Optional

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class ShopListDTO(ChatContextDTO):
    command_prefix: str
    command_buy_name: str


@dataclass(frozen=True)
class ShopBuyDTO(ChatContextDTO):
    item_name_input: Optional[str]
    command_prefix: str
    command_buy_name: str

