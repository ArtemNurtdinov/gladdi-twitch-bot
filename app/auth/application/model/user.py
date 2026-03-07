from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.auth.domain.model.role import UserRole


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
