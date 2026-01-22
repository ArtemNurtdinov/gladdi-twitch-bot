from datetime import datetime
from typing import Any
from uuid import UUID

from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.application.ports.token_service import TokenService
from app.auth.domain.models import AccessToken, User, UserCreateData, UserUpdateData
from app.auth.domain.repo import AuthRepository


class AuthService:
    def __init__(
        self,
        repo: AuthRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
    ):
        self._repo = repo
        self._password_hasher = password_hasher
        self._token_service = token_service

    def hash_password(self, password: str) -> str:
        return self._password_hasher.hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._password_hasher.verify_password(plain_password, hashed_password)

    def create_user_from_admin(self, user_data: UserCreateData) -> User:
        hashed_password = None
        if user_data.password:
            hashed_password = self.hash_password(user_data.password)

        return self._repo.create_user(user_data, hashed_password)

    def get_user_by_email(self, email: str) -> User | None:
        return self._repo.get_user_by_email(email)

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self._repo.get_user_by_id(user_id)

    def get_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self._repo.list_users(skip, limit)

    def update_user(self, user_id: UUID, user_data: UserUpdateData) -> User | None:
        updates = UserUpdateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_active=user_data.is_active,
            password=self.hash_password(user_data.password) if user_data.password else None,
        )
        return self._repo.update_user(user_id, updates)

    def delete_user(self, user_id: UUID) -> bool:
        return self._repo.delete_user(user_id)

    def authenticate_user(self, email: str, password: str) -> User | None:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_token(self, user: User) -> AccessToken:
        token_data = self._token_service.create_access_token(user)
        access_token = self._repo.create_token(user.id, token_data.token, token_data.expires_at)
        return access_token

    def validate_access_token(self, token: str) -> User | None:
        payload = self._token_service.validate_access_token(token)
        if not payload:
            return None

        current_time = datetime.utcnow()
        access_token = self._repo.find_active_token(token, current_time)

        if not access_token:
            return None

        user = self._repo.get_user_by_id(payload.user_id)
        if user and user.is_active:
            return user

        return None

    def verify_token(self, token: str) -> dict[str, Any] | None:
        payload = self._token_service.validate_access_token(token)
        if not payload:
            return None
        return {
            "sub": str(payload.user_id),
            "email": payload.email,
            "role": payload.role.value,
            "iat": payload.issued_at,
            "exp": payload.expires_at,
        }

    def get_tokens(self, skip: int = 0, limit: int = 100) -> list[AccessToken]:
        return self._repo.list_tokens(skip, limit)

    def get_token_by_id(self, token_id: UUID) -> AccessToken | None:
        return self._repo.get_token_by_id(token_id)

    def deactivate_token(self, token_id: UUID) -> bool:
        return self._repo.deactivate_token(token_id)

    def delete_token(self, token_id: UUID) -> bool:
        return self._repo.delete_token(token_id)
