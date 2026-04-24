import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from app.core.logger.domain.logger import Logger
from app.joke.application.model.post_joke import PostJokeDTO
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from app.task.domain.job import BackgroundJob


class PostJokeJob(BackgroundJob):
    name = "post_joke"
    _INTERVAL_DEFAULT = 60

    def __init__(
        self,
        handle_post_joke_use_case: HandlePostJokeUseCase,
        send_channel_message: Callable[[str], Awaitable[None]],
        logger: Logger,
    ):
        self._channel_name: str | None = None
        self._handle_post_joke_use_case = handle_post_joke_use_case
        self._send_channel_message = send_channel_message
        self._bot_name: str | None = None
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str) -> None:
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._INTERVAL_DEFAULT)

                post_joke = PostJokeDTO(
                    channel_name=self._channel_name,
                    bot_nick=self._bot_name.lower(),
                    occurred_at=datetime.now(UTC),
                )

                result = await self._handle_post_joke_use_case.handle(post_joke=post_joke)

                if result is None:
                    continue

                await self._send_channel_message(result)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                await asyncio.sleep(self._INTERVAL_DEFAULT)
