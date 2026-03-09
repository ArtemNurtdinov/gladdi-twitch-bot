from app.auth.application.dto import LoginResultDto
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.application.usecase.create_access_token_use_case import CreateAccessTokenUseCase
from app.auth.domain.auth_repository import AuthRepository


class LoginUseCase:
    def __init__(
        self,
        auth_repo: AuthRepository,
        password_hasher: PasswordHasher,
        create_access_token_use_case: CreateAccessTokenUseCase,
        user_mapper: UserMapper,
    ):
        self._repo = auth_repo
        self._password_hasher = password_hasher
        self._create_access_token_use_case = create_access_token_use_case
        self._user_mapper = user_mapper

    def login(self, email: str, password: str) -> LoginResultDto | None:
        user = self._repo.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not self._password_hasher.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        token = self._create_access_token_use_case.create_access_token(user)
        return LoginResultDto(
            access_token=token.token,
            created_at=token.created_at,
            expires_at=token.expires_at,
            user=self._user_mapper.map_user_to_dto(user),
        )
