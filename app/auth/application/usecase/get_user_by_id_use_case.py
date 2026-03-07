from uuid import UUID

from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.model.user import UserDTO
from app.auth.domain.auth_repository import AuthRepository


class GetUserByIdUseCase:
    def __init__(self, auth_repository: AuthRepository, user_mapper: UserMapper):
        self._auth_repository = auth_repository
        self._user_mapper = user_mapper

    def get_user_by_id(self, user_id: UUID) -> UserDTO | None:
        user = self._auth_repository.get_user_by_id(user_id)
        return self._user_mapper.map_user_to_dto(user) if user else None
