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
from app.core.config.domain.model.configuration import Config


def provide_user_mapper() -> UserMapper:
    return UserMapper()


def provide_token_mapper() -> TokenMapper:
    return TokenMapper()


def provide_auth_repository(session: Session) -> AuthRepository:
    return AuthRepositoryImpl(session)


def provide_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def provide_create_access_token_use_case(
    config: Config,
    auth_repository: AuthRepository,
    token_mapper: TokenMapper,
) -> CreateAccessTokenUseCase:
    return CreateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        access_token_expires_minutes=config.application.access_token_expire_minutes,
        auth_repo=auth_repository,
        token_mapper=token_mapper,
    )


def provide_validate_access_token_use_case(
    config: Config,
    auth_repository: AuthRepository,
    user_mapper: UserMapper,
) -> ValidateAccessTokenUseCase:
    return ValidateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        auth_repo=auth_repository,
        user_mapper=user_mapper,
    )


def provide_login_use_case(
    auth_repository: AuthRepository,
    password_hasher: PasswordHasher,
    create_access_token_use_case: CreateAccessTokenUseCase,
    user_mapper: UserMapper,
) -> LoginUseCase:
    return LoginUseCase(
        auth_repo=auth_repository,
        password_hasher=password_hasher,
        create_access_token_use_case=create_access_token_use_case,
        user_mapper=user_mapper,
    )
