from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.application.auth_service import AuthService
from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.ports.password_hasher import PasswordHasher
from app.auth.application.usecase.create_access_token_use_case import CreateAccessTokenUseCase
from app.auth.application.usecase.create_user_from_admin_use_case import CreateUserFromAdminUseCase
from app.auth.application.usecase.get_user_by_email_use_case import GetUserByEmailUseCase
from app.auth.application.usecase.get_user_by_id_use_case import GetUserByIdUseCase
from app.auth.application.usecase.get_users_use_case import GetUsersUseCase
from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.domain.auth_repository import AuthRepository
from app.auth.infrastructure.auth_repository import AuthRepositoryImpl
from app.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.core.config.di.composition import load_config
from app.core.config.domain.model.configuration import Config
from core.db import get_db


def provide_user_mapper() -> UserMapper:
    return UserMapper()


def provide_token_mapper() -> TokenMapper:
    return TokenMapper()


def get_auth_repository(session: Session = Depends(get_db)) -> AuthRepository:
    return AuthRepositoryImpl(session)


def provide_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_auth_service(
    user_mapper: UserMapper = Depends(provide_user_mapper),
    token_mapper: TokenMapper = Depends(provide_token_mapper),
    password_hasher: PasswordHasher = Depends(provide_password_hasher),
    auth_repository: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(
        repo=auth_repository,
        password_hasher=password_hasher,
        user_mapper=user_mapper,
        token_mapper=token_mapper,
    )


def provide_create_access_token_use_case(
    config: Config = Depends(load_config),
    auth_repository: AuthRepository = Depends(get_auth_repository),
    token_mapper: TokenMapper = Depends(provide_token_mapper),
) -> CreateAccessTokenUseCase:
    return CreateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        access_token_expires_minutes=config.application.access_token_expire_minutes,
        auth_repo=auth_repository,
        token_mapper=token_mapper,
    )


def provide_validate_access_token_use_case(
    config: Config = Depends(load_config),
    auth_repository: AuthRepository = Depends(get_auth_repository),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> ValidateAccessTokenUseCase:
    return ValidateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        auth_repo=auth_repository,
        user_mapper=user_mapper,
    )


def provide_login_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    password_hasher: PasswordHasher = Depends(provide_password_hasher),
    create_access_token_use_case: CreateAccessTokenUseCase = Depends(provide_create_access_token_use_case),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> LoginUseCase:
    return LoginUseCase(
        auth_repo=auth_repository,
        password_hasher=password_hasher,
        create_access_token_use_case=create_access_token_use_case,
        user_mapper=user_mapper,
    )


def get_user_by_id_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> GetUserByIdUseCase:
    return GetUserByIdUseCase(auth_repository=auth_repository, user_mapper=user_mapper)


def get_user_by_email_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> GetUserByEmailUseCase:
    return GetUserByEmailUseCase(auth_repository, user_mapper)


def get_users_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> GetUsersUseCase:
    return GetUsersUseCase(auth_repository, user_mapper)


def get_create_user_from_admin_use_case(
    auth_repository: AuthRepository = Depends(get_auth_repository),
    password_hasher: PasswordHasher = Depends(provide_password_hasher),
    user_mapper: UserMapper = Depends(provide_user_mapper),
) -> CreateUserFromAdminUseCase:
    return CreateUserFromAdminUseCase(
        password_hasher=password_hasher,
        auth_repo=auth_repository,
        user_mapper=user_mapper,
    )
