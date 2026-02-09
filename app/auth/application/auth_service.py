from datetime import datetime
from typing import Any
from uuid import UUID

from app.auth.application.dto import (
    LoginResultDto,
    TokenDto,
    UserCreateDto,
    UserDto,
    UserUpdateDto,
)
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

    def _to_user_dto(self, user: User) -> UserDto:
        return UserDto(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _to_token_dto(self, token: AccessToken) -> TokenDto:
        return TokenDto(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            is_active=token.is_active,
            created_at=token.created_at,
        )

    def _to_domain_create(self, user_data: UserCreateDto) -> UserCreateData:
        return UserCreateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active,
        )

    def _to_domain_update(self, user_data: UserUpdateDto) -> UserUpdateData:
        return UserUpdateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active,
        )

    def _create_token_for_user(self, user: User) -> TokenDto:
        token_data = self._token_service.create_access_token(user)
        access_token = self._repo.create_token(user.id, token_data.token, token_data.expires_at)
        return self._to_token_dto(access_token)

    def create_user_from_admin(self, user_data: UserCreateDto) -> UserDto:
        domain_input = self._to_domain_create(user_data)
        hashed_password = self.hash_password(user_data.password)

        user = self._repo.create_user(domain_input, hashed_password)
        return self._to_user_dto(user)

    def get_user_by_email(self, email: str) -> UserDto | None:
        user = self._repo.get_user_by_email(email)
        return self._to_user_dto(user) if user else None

    def get_user_by_id(self, user_id: UUID) -> UserDto | None:
        user = self._repo.get_user_by_id(user_id)
        return self._to_user_dto(user) if user else None

    def get_users(self, skip: int = 0, limit: int = 100) -> list[UserDto]:
        users = self._repo.list_users(skip, limit)
        return [self._to_user_dto(user) for user in users]

    def update_user(self, user_id: UUID, user_data: UserUpdateDto) -> UserDto | None:
        updates = self._to_domain_update(user_data)
        updates.password = self.hash_password(user_data.password) if user_data.password else None
        user = self._repo.update_user(user_id, updates)
        return self._to_user_dto(user) if user else None

    def delete_user(self, user_id: UUID) -> bool:
        return self._repo.delete_user(user_id)

    def _authenticate_user_domain(self, email: str, password: str) -> User | None:
        user = self._repo.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def authenticate_user(self, email: str, password: str) -> UserDto | None:
        user = self._authenticate_user_domain(email, password)
        return self._to_user_dto(user) if user else None

    def login(self, email: str, password: str) -> LoginResultDto | None:
        user = self._authenticate_user_domain(email, password)
        if not user:
            return None
        token = self._create_token_for_user(user)
        return LoginResultDto(
            access_token=token.token,
            created_at=token.created_at,
            expires_at=token.expires_at,
            user=self._to_user_dto(user),
        )

    def validate_access_token(self, token: str) -> UserDto | None:
        payload = self._token_service.validate_access_token(token)
        if not payload:
            return None

        current_time = datetime.utcnow()
        access_token = self._repo.find_active_token(token, current_time)

        if not access_token:
            return None

        user = self._repo.get_user_by_id(payload.user_id)
        if user and user.is_active:
            return self._to_user_dto(user)

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

    def get_tokens(self, skip: int = 0, limit: int = 100) -> list[TokenDto]:
        tokens = self._repo.list_tokens(skip, limit)
        return [self._to_token_dto(token) for token in tokens]

    def get_token_by_id(self, token_id: UUID) -> TokenDto | None:
        token = self._repo.get_token_by_id(token_id)
        return self._to_token_dto(token) if token else None

    def deactivate_token(self, token_id: UUID) -> bool:
        return self._repo.deactivate_token(token_id)

    def delete_token(self, token_id: UUID) -> bool:
        return self._repo.delete_token(token_id)
