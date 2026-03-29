from sqlalchemy.orm import Session

from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.di.dependencies import (
    provide_auth_repository,
    provide_create_access_token_use_case,
    provide_login_use_case,
    provide_password_hasher,
    provide_token_mapper,
    provide_user_mapper,
    provide_validate_access_token_use_case,
)
from app.core.config.di.composition import load_config


def get_validate_access_token_use_case(session: Session) -> ValidateAccessTokenUseCase:
    config = load_config()
    auth_repository = provide_auth_repository(session)
    user_mapper = provide_user_mapper()

    return provide_validate_access_token_use_case(config, auth_repository, user_mapper)


def get_login_use_case(session: Session) -> LoginUseCase:
    auth_repository = provide_auth_repository(session)
    password_hasher = provide_password_hasher()
    config = load_config()
    token_mapper = provide_token_mapper()
    user_mapper = provide_user_mapper()
    create_access_token_use_case = provide_create_access_token_use_case(config, auth_repository, token_mapper)
    return provide_login_use_case(auth_repository, password_hasher, create_access_token_use_case, user_mapper)
