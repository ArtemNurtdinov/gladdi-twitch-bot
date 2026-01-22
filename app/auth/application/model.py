from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.auth.domain.models import UserRole


@dataclass(frozen=True)
class TokenPayload:
    user_id: UUID
    email: str
    role: UserRole
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class TokenData:
    token: str
    expires_at: datetime