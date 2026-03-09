from datetime import datetime
from uuid import UUID

from jose import JWTError, jwt
from jose import exceptions as jose_exceptions

from app.auth.application.dto import UserDto
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.model import TokenPayload
from app.auth.domain.auth_repository import AuthRepository
from app.auth.domain.model.role import UserRole


class ValidateAccessTokenUseCase:
    def __init__(self, secret: str, algorithm: str, auth_repo: AuthRepository, user_mapper: UserMapper):
        self._secret = secret
        self._algorithm = algorithm
        self._auth_repo = auth_repo
        self._user_mapper = user_mapper

    def validate_access_token(self, token: str) -> UserDto | None:
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

            payload = TokenPayload(
                user_id=UUID(user_id_raw),
                email=email,
                role=UserRole(role_raw),
                issued_at=issued_at,
                expires_at=expires_at,
            )

            current_time = datetime.utcnow()
            access_token = self._auth_repo.find_active_token(token, current_time)
            if not access_token:
                return None

            user = self._auth_repo.get_user_by_id(payload.user_id)
            if user and user.is_active:
                return self._user_mapper.map_user_to_dto(user)

            return None
        except (JWTError, jose_exceptions.JWTError, jose_exceptions.ExpiredSignatureError):
            return None
        except Exception:
            return None
