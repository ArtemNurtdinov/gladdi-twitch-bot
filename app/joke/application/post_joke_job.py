import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.joke.application.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.model import PostJokeDTO
from core.background.task_runner import BackgroundTaskRunner


class PostJokeJob:
    name = "post_joke"

    def __init__(
        self,
        channel_name: str,
        handle_post_joke_use_case: HandlePostJokeUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        send_channel_message: Callable[[str, str], Awaitable[None]],
        bot_nick: str,
    ):
        self._channel_name = channel_name
        self._handle_post_joke_use_case = handle_post_joke_use_case
        self._db_session_provider = db_session_provider
        self._send_channel_message = send_channel_message
        self._bot_nick = bot_nick

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(30)

                post_joke = PostJokeDTO(
                    channel_name=self._channel_name,
                    bot_nick=self._bot_nick.lower(),
                    occurred_at=datetime.utcnow(),
                )

                result = await self._handle_post_joke_use_case.handle(
                    db_session_provider=self._db_session_provider,
                    post_joke=post_joke,
                )
                if result is None:
                    continue

                await self._send_channel_message(self._channel_name, result)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
