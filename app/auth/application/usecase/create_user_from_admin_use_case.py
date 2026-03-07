from app.auth.application.dto import UserCreateDto
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.model.user import UserDTO
from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.domain.auth_repository import AuthRepository
from app.auth.domain.models import UserCreateData


class CreateUserFromAdminUseCase:
    def __init__(self, password_hasher: PasswordHasher, auth_repo: AuthRepository, user_mapper: UserMapper):
        self._password_hasher = password_hasher
        self._auth_repo = auth_repo
        self._user_mapper = user_mapper

    def create_user(self, user_data: UserCreateDto) -> UserDTO:
        user_create = self._map_user_create_to_domain(user_data)
        hashed_password = self._password_hasher.hash_password(user_data.password)
        user = self._auth_repo.create_user(user_create, hashed_password)
        return self._user_mapper.map_user_to_dto(user)

    def _map_user_create_to_domain(self, user_data: UserCreateDto) -> UserCreateData:
        return UserCreateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active,
        )
