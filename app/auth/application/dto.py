from dataclasses import dataclass

from app.auth.domain.model.role import UserRole


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
