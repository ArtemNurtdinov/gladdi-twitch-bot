from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.auth.domain.models import UserRole


@dataclass(frozen=True)
class UserDto:
    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TokenDto:
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class LoginResultDto:
    access_token: str
    created_at: datetime
    expires_at: datetime
    user: UserDto


@dataclass
class UserCreateDto:
    email: str
    first_name: str
    last_name: str
    password: str
    role: UserRole
    is_active: bool


@dataclass
class UserUpdateDto:
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
