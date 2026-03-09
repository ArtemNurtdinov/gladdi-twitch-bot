from app.auth.application.dto import UserDto
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.domain.repo import AuthRepository


class GetUsersUseCase:
    def __init__(self, auth_repo: AuthRepository, user_mapper: UserMapper):
        self._auth_repo = auth_repo
        self._user_mapper = user_mapper

    def get_users(self, skip: int, limit: int) -> list[UserDto]:
        users = self._auth_repo.list_users(skip, limit)
        return [self._user_mapper.map_user_to_dto(user) for user in users]
