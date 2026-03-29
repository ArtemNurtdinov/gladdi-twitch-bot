from functools import lru_cache

from app.auth.application.auth_service import AuthService
from app.auth.application.mapper.token_mapper import TokenMapper
from app.auth.application.mapper.user_mapper import UserMapper
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
from app.core.config.application.usecase.load_configuration_use_case import LoadConfigurationUseCase
from app.core.config.application.usecase.validate_config_use_case import ValidateConfigUseCase
from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.domain.model.configuration import Config
from app.core.config.infrastructure.config_repository import ConfigRepositoryImpl
from app.core.config.infrastructure.config_source import EnvConfigSource
from app.core.logger.domain.logger import Logger
from app.core.logger.infrastructure.logger import LoggerImpl
from app.platform.bot.bot_manager import BotManager
from app.platform.bot.model.bot_settings import BotSettings, DefaultBotSettings
from core.db import get_db


@lru_cache
def get_logger() -> Logger:
    config = load_config()
    return LoggerImpl("bootstrap", config.logging)


def get_config_source() -> ConfigSource:
    return EnvConfigSource()


def get_config_repository() -> ConfigRepository:
    source: ConfigSource = get_config_source()
    return ConfigRepositoryImpl(source)


def get_validate_config_use_case() -> ValidateConfigUseCase:
    return ValidateConfigUseCase()


def get_load_configuration_use_case() -> LoadConfigurationUseCase:
    config_repository: ConfigRepository = get_config_repository()
    validate_config_use_case: ValidateConfigUseCase = get_validate_config_use_case()
    return LoadConfigurationUseCase(config_repository, validate_config_use_case)


@lru_cache
def load_config() -> Config:
    load_configuration_use_case: LoadConfigurationUseCase = get_load_configuration_use_case()
    return load_configuration_use_case.execute()


@lru_cache
def get_bot_settings() -> BotSettings:
    config = load_config()
    group_id = config.telegram.group_id
    settings = DefaultBotSettings(group_id=group_id)
    return settings


@lru_cache
def get_bot_manager() -> BotManager:
    settings = get_bot_settings()
    logger = get_logger()
    return BotManager(settings=settings, logger=logger)


def get_auth_repository() -> AuthRepository:
    db = get_db()
    return AuthRepositoryImpl(db)


def get_user_mapper() -> UserMapper:
    return UserMapper()


def get_token_mapper() -> TokenMapper:
    return TokenMapper()


def get_auth_service() -> AuthService:
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    token_mapper = get_token_mapper()
    return AuthService(
        repo=auth_repository,
        password_hasher=BcryptPasswordHasher(),
        user_mapper=user_mapper,
        token_mapper=token_mapper,
    )


def get_create_access_token_use_case() -> CreateAccessTokenUseCase:
    config = load_config()
    auth_repository = get_auth_repository()
    token_mapper = TokenMapper()
    return CreateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        access_token_expires_minutes=config.application.access_token_expire_minutes,
        auth_repo=auth_repository,
        token_mapper=token_mapper,
    )


def get_validate_access_token_use_case() -> ValidateAccessTokenUseCase:
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    config = load_config()
    return ValidateAccessTokenUseCase(
        secret=config.application.auth_secret,
        algorithm=config.application.auth_secret_algorithm,
        auth_repo=auth_repository,
        user_mapper=user_mapper,
    )


def get_login_use_case() -> LoginUseCase:
    create_access_token_use_case = get_create_access_token_use_case()
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    return LoginUseCase(
        auth_repo=auth_repository,
        password_hasher=BcryptPasswordHasher(),
        create_access_token_use_case=create_access_token_use_case,
        user_mapper=user_mapper,
    )


def get_user_by_id_use_case() -> GetUserByIdUseCase:
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    return GetUserByIdUseCase(auth_repository=auth_repository, user_mapper=user_mapper)


def get_user_by_email_use_case() -> GetUserByEmailUseCase:
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    return GetUserByEmailUseCase(auth_repository, user_mapper)


def get_users_use_case() -> GetUsersUseCase:
    auth_repo = get_auth_repository()
    user_mapper = get_user_mapper()
    return GetUsersUseCase(auth_repo, user_mapper)


def get_create_user_from_admin_use_case() -> CreateUserFromAdminUseCase:
    auth_repository = get_auth_repository()
    user_mapper = get_user_mapper()
    return CreateUserFromAdminUseCase(
        password_hasher=BcryptPasswordHasher(),
        auth_repo=auth_repository,
        user_mapper=user_mapper,
    )
