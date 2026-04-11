from abc import ABC
from dataclasses import dataclass
from datetime import datetime

from app.auth.application.model.user import UserDTO


@dataclass(frozen=True)
class LoginResult(ABC):
    pass


@dataclass(frozen=True)
class LoginSuccess(LoginResult):
    access_token: str
    created_at: datetime
    expires_at: datetime
    user: UserDTO


@dataclass(frozen=True)
class UserNotFound(LoginResult):
    pass


@dataclass(frozen=True)
class InvalidPassword(LoginResult):
    pass


@dataclass(frozen=True)
class UserInactive(LoginResult):
    pass


LoginResultDTO = LoginSuccess | UserNotFound | InvalidPassword | UserInactive
