import calendar
from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from jose import exceptions as jose_exceptions

from app.auth.application.model import TokenData, TokenPayload
from app.auth.application.ports.token_service import TokenService
from app.auth.domain.models import User, UserRole


class JwtTokenService(TokenService):
    def __init__(self, secret: str, algorithm: str, access_token_expires_minutes: int):
        self._secret = secret
        self._algorithm = algorithm
        self._access_token_expires_minutes = access_token_expires_minutes

    def create_access_token(self, user: User) -> TokenData:
        issued_at_utc = datetime.utcnow()
        expires_at_utc = issued_at_utc + timedelta(minutes=self._access_token_expires_minutes)

        issued_at_timestamp = calendar.timegm(issued_at_utc.timetuple())
        expires_at_timestamp = calendar.timegm(expires_at_utc.timetuple())

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "iat": issued_at_timestamp,
            "exp": expires_at_timestamp,
        }

        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return TokenData(token=token, expires_at=expires_at_utc)

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
