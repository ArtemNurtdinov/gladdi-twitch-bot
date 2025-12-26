import asyncio
import logging
from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.background.chat_summary.dto import ChatSummarizerDTO
from app.twitch.application.background.chat_summary.handle_chat_summarizer_use_case import (
    HandleChatSummarizerUseCase,
)
from app.twitch.application.background.state import ChatSummaryState
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class ChatSummarizerJob:
    name = "summarize_chat"

    def __init__(
        self,
        channel_name: str,
        twitch_api_service: TwitchApiService,
        handle_chat_summarizer_use_case: HandleChatSummarizerUseCase,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        state: ChatSummaryState,
    ):
        self._channel_name = channel_name
        self._twitch_api_service = twitch_api_service
        self._handle_chat_summarizer_use_case = handle_chat_summarizer_use_case
        self._db_readonly_session_provider = db_readonly_session_provider
        self._state = state

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(20 * 60)

                chat_summarizer_dto = ChatSummarizerDTO(
                    channel_name=self._channel_name,
                    occurred_at=datetime.utcnow(),
                    interval_minutes=20,
                )

                result = await self._handle_chat_summarizer_use_case.handle(
                    db_readonly_session_provider=self._db_readonly_session_provider,
                    chat_summarizer=chat_summarizer_dto
                )
                if result is None:
                    logger.debug("Нет данных для анализа или стрим не активен")
                    continue
                self._state.current_stream_summaries.append(result)
                self._state.last_chat_summary_time = datetime.utcnow()
                logger.info(f"Создан периодический анализ чата: {result}")
            except asyncio.CancelledError:
                logger.info("ChatSummarizerJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ChatSummarizerJob: {e}")

