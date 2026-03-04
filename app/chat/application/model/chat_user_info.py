from dataclasses import dataclass


@dataclass
class ChatUserInfo:
    channel_name: str
    username: str
    message_count: int
