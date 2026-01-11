from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TransferDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    recipient_input: str | None
    amount_input: str | None
