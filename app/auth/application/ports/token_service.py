from typing import Protocol

from app.auth.application.model import TokenData, TokenPayload
from app.auth.domain.models import User


class TokenService(Protocol):
    def create_access_token(self, user: User) -> TokenData: ...

    def validate_access_token(self, token: str) -> TokenPayload | None: ...
