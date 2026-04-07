from sqlalchemy.orm import Session

from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.application.usecase.create_access_token_use_case import CreateAccessTokenUseCase
from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.domain.auth_repository import AuthRepository
from app.auth.infrastructure.auth_repository import AuthRepositoryImpl
from app.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.core.config.domain.model.application import ApplicationConfig


class AuthContainer:
    def __init__(self, application_config: ApplicationConfig):
        self.application_config = application_config
        self.user_mapper = UserMapper()

    def _get_repository(self, session: Session) -> AuthRepository:
        return AuthRepositoryImpl(session)

    def validate_access_token_use_case(self, session: Session) -> ValidateAccessTokenUseCase:
        auth_repository = self._get_repository(session)
        return ValidateAccessTokenUseCase(
            self.application_config.auth_secret, self.application_config.auth_secret_algorithm, auth_repository, self.user_mapper
        )

    def create_access_token_use_case(self, session: Session) -> CreateAccessTokenUseCase:
        auth_repository = self._get_repository(session)
        token_mapper = TokenMapper()
        return CreateAccessTokenUseCase(
            self.application_config.auth_secret,
            self.application_config.auth_secret_algorithm,
            self.application_config.access_token_expire_minutes,
            auth_repository,
            token_mapper,
        )

    def login_use_case(self, session: Session) -> LoginUseCase:
        auth_repository = self._get_repository(session)
        password_hasher: PasswordHasher = BcryptPasswordHasher()
        create_access_token_use_case = self.create_access_token_use_case(session)
        return LoginUseCase(auth_repository, password_hasher, create_access_token_use_case, self.user_mapper)
