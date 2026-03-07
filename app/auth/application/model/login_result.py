from dataclasses import dataclass
from datetime import datetime

from app.auth.application.model.user import UserDTO


@dataclass(frozen=True)
class LoginResultDTO:
    access_token: str
    created_at: datetime
    expires_at: datetime
    user: UserDTO
