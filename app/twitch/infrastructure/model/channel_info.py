from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChannelInfo:
    broadcaster_id: str
    broadcaster_login: str
    broadcaster_name: str
    broadcaster_language: str
    game_id: str
    game_name: str
    title: str
    delay: int
    tags: List[str]
    content_classification_labels: Optional[List[str]] = None
    is_branded_content: bool = False 