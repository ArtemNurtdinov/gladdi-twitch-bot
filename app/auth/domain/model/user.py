from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.auth.domain.model.role import UserRole


@dataclass
class User:
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    hashed_password: str | None
    created_at: datetime
    updated_at: datetime
