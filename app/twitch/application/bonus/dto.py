from dataclasses import dataclass

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class BonusDTO(ChatContextDTO):
    pass
