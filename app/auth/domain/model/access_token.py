from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AccessToken:
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime
