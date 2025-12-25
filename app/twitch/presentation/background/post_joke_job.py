import asyncio
from datetime import datetime
from typing import Callable, Awaitable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.background.post_joke.dto import PostJokeDTO
from app.twitch.application.background.post_joke.handle_post_joke_use_case import HandlePostJokeUseCase
from core.background_task_runner import BackgroundTaskRunner


class PostJokeJob:
    name = "post_joke"

    def __init__(
        self,
        channel_name: str,
        handle_post_joke_use_case: HandlePostJokeUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        send_channel_message: Callable[[str, str], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
    ):
        self._channel_name = channel_name
        self._handle_post_joke_use_case = handle_post_joke_use_case
        self._db_session_provider = db_session_provider
        self._send_channel_message = send_channel_message
        self._bot_nick_provider = bot_nick_provider

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(30)

                dto = PostJokeDTO(
                    channel_name=self._channel_name,
                    display_name="",
                    user_name="",
                    bot_nick=self._bot_nick_provider().lower(),
                    occurred_at=datetime.utcnow(),
                )

                result = await self._handle_post_joke_use_case.handle(
                    db_session_provider=self._db_session_provider,
                    dto=dto,
                )
                if result is None:
                    continue

                await self._send_channel_message(self._channel_name, result)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
