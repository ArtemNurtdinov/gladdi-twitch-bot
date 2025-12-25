from dataclasses import dataclass
from typing import Optional

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class RpsDTO(ChatContextDTO):
    choice_input: Optional[str]

