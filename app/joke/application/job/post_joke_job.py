import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.joke.application.model.post_joke import PostJokeDTO
from app.joke.application.usecase.handle_post_joke_use_case import HandlePostJokeUseCase
from core.background.task_runner import BackgroundTaskRunner
from core.background.tasks import BackgroundJob


class PostJokeJob(BackgroundJob):
    name = "post_joke"

    def __init__(
        self,
        channel_name: str,
        handle_post_joke_use_case: HandlePostJokeUseCase,
        send_channel_message: Callable[[str], Awaitable[None]],
        bot_name: str,
    ):
        self._channel_name = channel_name
        self._handle_post_joke_use_case = handle_post_joke_use_case
        self._send_channel_message = send_channel_message
        self._bot_name = bot_name

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(30)

                post_joke = PostJokeDTO(
                    channel_name=self._channel_name,
                    bot_nick=self._bot_name.lower(),
                    occurred_at=datetime.utcnow(),
                )

                result = await self._handle_post_joke_use_case.handle(post_joke=post_joke)
                if result is None:
                    continue

                await self._send_channel_message(result)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
