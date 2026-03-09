from uuid import UUID

from app.auth.application.dto import (
    TokenDto,
    UserDto,
    UserUpdateDto,
)
from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.domain.auth_repository import AuthRepository
from app.auth.domain.models import UserUpdateData


class AuthService:
    def __init__(
        self,
        repo: AuthRepository,
        password_hasher: PasswordHasher,
        user_mapper: UserMapper,
        token_mapper: TokenMapper,
    ):
        self._repo = repo
        self._password_hasher = password_hasher
        self._user_mapper = user_mapper
        self._token_mapper = token_mapper

    def _to_domain_update(self, user_data: UserUpdateDto) -> UserUpdateData:
        return UserUpdateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active,
        )

    def update_user(self, user_id: UUID, user_data: UserUpdateDto) -> UserDto | None:
        updates = self._to_domain_update(user_data)
        updates.password = self._password_hasher.hash_password(user_data.password) if user_data.password else None
        user = self._repo.update_user(user_id, updates)
        return self._user_mapper.map_user_to_dto(user) if user else None

    def delete_user(self, user_id: UUID) -> bool:
        return self._repo.delete_user(user_id)

    def get_tokens(self, skip: int = 0, limit: int = 100) -> list[TokenDto]:
        tokens = self._repo.list_tokens(skip, limit)
        return [self._token_mapper.map_token_to_dto(token) for token in tokens]

    def get_token_by_id(self, token_id: UUID) -> TokenDto | None:
        token = self._repo.get_token_by_id(token_id)
        return self._token_mapper.map_token_to_dto(token) if token else None

    def deactivate_token(self, token_id: UUID) -> bool:
        return self._repo.deactivate_token(token_id)

    def delete_token(self, token_id: UUID) -> bool:
        return self._repo.delete_token(token_id)
