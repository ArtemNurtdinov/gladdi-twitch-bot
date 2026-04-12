from app.core.logger.domain.logger import Logger
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.application.usecase.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.auth.infrastructure.twitch_auth import TwitchAuth


class PlatformAuthContainer:
    def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str, logger: Logger):
        self.platform_auth = TwitchAuth(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            logger=logger,
        )
        self.handle_token_checker_use_case = HandleTokenCheckerUseCase(self.platform_auth, logger)
        self.token_checker_job = TokenCheckerJob(self.handle_token_checker_use_case, logger)
