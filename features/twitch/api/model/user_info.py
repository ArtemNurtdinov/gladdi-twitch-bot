from dataclasses import dataclass
from typing import Optional


@dataclass
class UserInfo:
    id: str
    login: str
    display_name: str
    type: str = ""
    broadcaster_type: str = ""
    description: str = ""
    profile_image_url: str = ""
    offline_image_url: str = ""
    view_count: int = 0
    email: Optional[str] = None
    created_at: Optional[str] = None 