from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    channel_name: str
    user_name: str
    content: str
    created_at: datetime

