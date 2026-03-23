from dataclasses import dataclass

from app.platform.command.dto import ChatContextDTO


@dataclass(frozen=True)
class RpsDTO(ChatContextDTO):
    command_prefix: str
    command_name: str
    choice_input: str | None
