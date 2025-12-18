from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatMessage:
    channel_name: str
    user_name: str
    content: str
    created_at: datetime


@dataclass
class TopChatUserInfo:
    channel_name: str
    username: str
    message_count: int
