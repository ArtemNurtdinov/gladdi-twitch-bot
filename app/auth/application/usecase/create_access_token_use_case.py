import calendar
from datetime import datetime, timedelta

from jose import jwt

from app.auth.application.dto import TokenDto
from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.model import TokenData
from app.auth.domain.auth_repository import AuthRepository
from app.auth.domain.model.user import User


class CreateAccessTokenUseCase:
    def __init__(
        self, secret: str, algorithm: str, access_token_expires_minutes: int, auth_repo: AuthRepository, token_mapper: TokenMapper
    ):
        self._secret = secret
        self._algorithm = algorithm
        self._access_token_expires_minutes = access_token_expires_minutes
        self._auth_repo = auth_repo
        self._token_mapper = token_mapper

    def create_access_token(self, user: User) -> TokenDto:
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
        token_data = TokenData(token=token, expires_at=expires_at_utc)

        access_token = self._auth_repo.create_token(user.id, token_data.token, token_data.expires_at)

        return self._token_mapper.map_token_to_dto(access_token)
