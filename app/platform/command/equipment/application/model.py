from dataclasses import dataclass

from app.platform.command.dto import ChatContextDTO


@dataclass(frozen=True)
class EquipmentDTO(ChatContextDTO):
    command_prefix: str
    command_name: str
    command_shop: str
