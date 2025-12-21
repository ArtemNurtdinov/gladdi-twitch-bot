from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool
    hashed_password: Optional[str]
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
    first_name: Optional[str]
    last_name: Optional[str]
    password: Optional[str]
    role: UserRole
    is_active: bool = True


@dataclass
class UserUpdateData:
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

