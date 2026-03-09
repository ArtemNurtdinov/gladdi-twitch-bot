from typing import Protocol

from app.auth.application.model import TokenPayload


class TokenService(Protocol):
    def validate_access_token(self, token: str) -> TokenPayload | None: ...
