from dataclasses import dataclass
from typing import Optional

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class RpsDTO(ChatContextDTO):
    choice_input: Optional[str]

