from dataclasses import dataclass

from app.auth.domain.model.role import UserRole


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
