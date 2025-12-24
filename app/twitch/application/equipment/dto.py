from dataclasses import dataclass

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class EquipmentDTO(ChatContextDTO):
    command_prefix: str
    command_shop: str

