from datetime import datetime
from uuid import UUID

from jose import JWTError, jwt
from jose import exceptions as jose_exceptions

from app.auth.application.model import TokenPayload
from app.auth.domain.model.role import UserRole


class ValidateAccessTokenUseCase:
    def __init__(self, secret: str, algorithm: str):
        self._secret = secret
        self._algorithm = algorithm

    def validate_access_token(self, token: str) -> TokenPayload | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])

            user_id_raw = payload.get("sub")
            email = payload.get("email")
            role_raw = payload.get("role")
            iat = payload.get("iat")
            exp = payload.get("exp")
            if not user_id_raw or not email or not role_raw or not iat or not exp:
                return None

            issued_at = datetime.utcfromtimestamp(iat)
            expires_at = datetime.utcfromtimestamp(exp)

            return TokenPayload(
                user_id=UUID(user_id_raw),
                email=email,
                role=UserRole(role_raw),
                issued_at=issued_at,
                expires_at=expires_at,
            )
        except (JWTError, jose_exceptions.JWTError, jose_exceptions.ExpiredSignatureError):
            return None
        except Exception:
            return None
