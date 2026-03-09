from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.application.auth_service import AuthService
from app.auth.application.dto import UserDto, UserRole
from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.mapper.user_mapper import UserMapper
from app.auth.application.usecase.create_access_token_use_case import CreateAccessTokenUseCase
from app.auth.application.usecase.create_user_from_admin_use_case import CreateUserFromAdminUseCase
from app.auth.application.usecase.get_user_by_email_use_case import GetUserByEmailUseCase
from app.auth.application.usecase.get_user_by_id_use_case import GetUserByIdUseCase
from app.auth.application.usecase.get_users_use_case import GetUsersUseCase
from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.infrastructure.auth_repository import AuthRepositoryImpl
from app.auth.infrastructure.password_hasher import BcryptPasswordHasher
from bootstrap.config_provider import get_config
from core.config import Config
from core.db import get_db

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_auth_service(
    session: Session = Depends(get_db),
) -> AuthService:
    user_mapper = UserMapper()
    token_mapper = TokenMapper()
    auth_repo = AuthRepositoryImpl(session)
    return AuthService(
        repo=auth_repo,
        password_hasher=BcryptPasswordHasher(),
        user_mapper=user_mapper,
        token_mapper=token_mapper,
    )


def get_create_access_token_use_case(
    session: Session = Depends(get_db),
    config: Config = Depends(get_config),
) -> CreateAccessTokenUseCase:
    token_mapper = TokenMapper()
    return CreateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        access_token_expires_minutes=config.application.access_token_expire_minutes,
        auth_repo=AuthRepositoryImpl(session),
        token_mapper=token_mapper,
    )


def get_validate_access_token_use_case(
    session: Session = Depends(get_db),
    config: Config = Depends(get_config),
) -> ValidateAccessTokenUseCase:
    auth_repo = AuthRepositoryImpl(session)
    return ValidateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        auth_repo=auth_repo,
        user_mapper=UserMapper(),
    )


def get_login_use_case(
    session: Session = Depends(get_db),
    create_access_token_use_case: CreateAccessTokenUseCase = Depends(get_create_access_token_use_case),
) -> LoginUseCase:
    auth_repo = AuthRepositoryImpl(session)
    return LoginUseCase(
        auth_repo=auth_repo,
        password_hasher=BcryptPasswordHasher(),
        create_access_token_use_case=create_access_token_use_case,
        user_mapper=UserMapper(),
    )


def get_user_by_id_use_case(
    session: Session = Depends(get_db),
) -> GetUserByIdUseCase:
    auth_repo = AuthRepositoryImpl(session)
    return GetUserByIdUseCase(auth_repository=auth_repo, user_mapper=UserMapper())


def get_user_by_email_use_case(
    session: Session = Depends(get_db),
) -> GetUserByEmailUseCase:
    auth_repo = AuthRepositoryImpl(session)
    user_mapper = UserMapper()
    return GetUserByEmailUseCase(auth_repo, user_mapper)


def get_users_use_case(
    session: Session = Depends(get_db),
) -> GetUsersUseCase:
    auth_repo = AuthRepositoryImpl(session)
    user_mapper = UserMapper()
    return GetUsersUseCase(auth_repo, user_mapper)


def get_create_user_from_admin_use_case(
    session: Session = Depends(get_db),
) -> CreateUserFromAdminUseCase:
    auth_repo = AuthRepositoryImpl(session)
    return CreateUserFromAdminUseCase(
        password_hasher=BcryptPasswordHasher(),
        auth_repo=auth_repo,
        user_mapper=UserMapper(),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(get_validate_access_token_use_case),
) -> UserDto:
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_admin_user(current_user: UserDto = Depends(get_current_user)) -> UserDto:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа")
    return current_user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(get_validate_access_token_use_case),
) -> UserDto | None:
    if credentials is None:
        return None
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user
