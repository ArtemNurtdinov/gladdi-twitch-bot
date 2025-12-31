from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


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


@dataclass
class AccessToken:
    id: UUID
    user_id: UUID
    token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime


@dataclass
class UserCreateData:
    email: str
    first_name: str | None
    last_name: str | None
    password: str | None
    role: UserRole
    is_active: bool = True


@dataclass
class UserUpdateData:
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
