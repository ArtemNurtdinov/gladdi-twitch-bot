import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from app.core.logger.domain.logger import Logger
from app.periodic_message.application.model.post_periodic_messages import PostPeriodicMessagesDTO
from app.periodic_message.application.usecase.handle_post_periodic_messages_use_case import HandlePostPeriodicMessagesUseCase
from app.task.domain.job import BackgroundJob


class PostPeriodicMessagesJob(BackgroundJob):
    name = "post_periodic_messages"
    _INTERVAL_DEFAULT = 60

    def __init__(
        self,
        handle_post_periodic_messages_use_case: HandlePostPeriodicMessagesUseCase,
        send_channel_message: Callable[[str], Awaitable[None]],
        logger: Logger,
    ):
        self._channel_name: str | None = None
        self._bot_name: str | None = None
        self._handle_post_periodic_messages_use_case = handle_post_periodic_messages_use_case
        self._send_channel_message = send_channel_message
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str) -> None:
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._INTERVAL_DEFAULT)

                occurred_at = datetime.now(UTC)
                bot_nick = self._bot_name.lower()
                payload = PostPeriodicMessagesDTO(
                    channel_name=self._channel_name,
                    bot_nick=bot_nick,
                    occurred_at=occurred_at,
                )

                prepared_messages = await self._handle_post_periodic_messages_use_case.handle(payload)

                for prepared in prepared_messages:
                    try:
                        await self._send_channel_message(prepared.text)
                        await self._handle_post_periodic_messages_use_case.mark_sent(
                            message_id=prepared.message_id,
                            interval_minutes=prepared.interval_minutes,
                            channel_name=self._channel_name,
                            bot_nick=bot_nick,
                            text=prepared.text,
                            use_llm=prepared.use_llm,
                            prompt=prepared.prompt,
                            occurred_at=occurred_at,
                        )
                    except Exception as e:
                        self._logger.log_exception(f"error while sending periodic message id={prepared.message_id}", e)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                await asyncio.sleep(self._INTERVAL_DEFAULT)
