from dataclasses import dataclass
from typing import Optional

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class TransferDTO(ChatContextDTO):
    recipient_input: Optional[str]
    amount_input: Optional[str]
    command_prefix: str
    command_name: str

