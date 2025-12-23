import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Any

from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.presentation.background.bot_tasks import ChatSummaryState
from core.background_task_runner import BackgroundTaskRunner
from core.db import db_ro_session

logger = logging.getLogger(__name__)


class ChatSummarizerJob:
    name = "summarize_chat"

    def __init__(
        self,
        channel_name: str,
        user_cache: Any,
        twitch_api_service: TwitchApiService,
        stream_service_factory: Callable[[Any], Any],
        chat_use_case_factory: Callable[[Any], Any],
        generate_response_in_chat: Callable[[str, str], str],
        state: ChatSummaryState,
    ):
        self._channel_name = channel_name
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._stream_service_factory = stream_service_factory
        self._chat_use_case_factory = chat_use_case_factory
        self._generate_response_in_chat = generate_response_in_chat
        self._state = state

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(20 * 60)

                with db_ro_session() as db:
                    active_stream = self._stream_service_factory(db).get_active_stream(self._channel_name)
                if not active_stream:
                    logger.debug("Стрим не активен, пропускаем анализ чата")
                    continue

                since = datetime.utcnow() - timedelta(minutes=20)
                with db_ro_session() as db:
                    messages = self._chat_use_case_factory(db).get_last_chat_messages_since(self._channel_name, since)

                if not messages:
                    logger.debug("Нет сообщений для анализа")
                    continue

                chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
                prompt = (
                    f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                    f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
                )
                result = self._generate_response_in_chat(prompt, self._channel_name)
                self._state.current_stream_summaries.append(result)
                self._state.last_chat_summary_time = datetime.utcnow()
                logger.info(f"Создан периодический анализ чата: {result}")
            except asyncio.CancelledError:
                logger.info("ChatSummarizerJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в ChatSummarizerJob: {e}")

