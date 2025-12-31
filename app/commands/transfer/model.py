from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TransferDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    recipient_input: Optional[str]
    amount_input: Optional[str]
