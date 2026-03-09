from app.auth.application.dto import UserDto
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.domain.auth_repository import AuthRepository


class GetUserByEmailUseCase:
    def __init__(self, auth_repository: AuthRepository, user_mapper: UserMapper):
        self._auth_repository = auth_repository
        self._user_mapper = user_mapper

    def get_user_by_email(self, email: str) -> UserDto | None:
        user = self._auth_repository.get_user_by_email(email)
        return self._user_mapper.map_user_to_dto(user) if user else None
