from app.core.logger.domain.logger import Logger
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.auth.infrastructure.twitch_auth import TwitchAuth
from app.platform.auth.platform_auth import PlatformAuth


def provide_platform_auth(access_token: str, refresh_token: str, client_id: str, client_secret: str, logger: Logger) -> PlatformAuth:
    return TwitchAuth(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        logger=logger,
    )


def provide_handle_token_checker_use_case(platform_auth: PlatformAuth, logger: Logger) -> HandleTokenCheckerUseCase:
    return HandleTokenCheckerUseCase(platform_auth=platform_auth, logger=logger)


def provide_token_checker_job(handle_token_checker_use_case: HandleTokenCheckerUseCase, logger: Logger) -> TokenCheckerJob:
    return TokenCheckerJob(handle_token_checker_use_case, logger)
