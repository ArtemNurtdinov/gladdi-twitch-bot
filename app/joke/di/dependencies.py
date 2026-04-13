from collections.abc import Awaitable, Callable

from app.core.logger.domain.logger import Logger
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase


def provide_post_joke_job(
    channel_name: str,
    handle_post_joke_use_case: HandlePostJokeUseCase,
    send_channel_message: Callable[[str], Awaitable[None]],
    bot_name: str,
    logger: Logger,
) -> PostJokeJob:
    return PostJokeJob(
        channel_name=channel_name,
        handle_post_joke_use_case=handle_post_joke_use_case,
        send_channel_message=send_channel_message,
        bot_name=bot_name,
        logger=logger,
    )
