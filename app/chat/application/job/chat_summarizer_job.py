import asyncio
from datetime import UTC, datetime

from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.model.summarizer_job import SummarizerJobDTO
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.core.logger.domain.logger import Logger
from app.task.domain.job import BackgroundJob


class ChatSummarizerJob(BackgroundJob):
    name = "summarize_chat"
    _INTERVAL_DEFAULT = 20 * 60

    def __init__(self, handle_chat_summarizer_use_case: HandleChatSummarizerUseCase, chat_summary_state: ChatSummaryState, logger: Logger):
        self._handle_chat_summarizer_use_case = handle_chat_summarizer_use_case
        self._logger = logger.create_child(__name__)
        self._channel_name: str | None = None
        self._bot_name: str | None = None
        self._chat_summary_state = chat_summary_state

    def apply_channel(self, channel_name: str, bot_name: str):
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._INTERVAL_DEFAULT)

                occurred_at = datetime.now(UTC)
                since = self._chat_summary_state.last_chat_summary_time
                summarizer_job_dto = SummarizerJobDTO(channel_name=self._channel_name, occurred_at=occurred_at, since=since)

                result = await self._handle_chat_summarizer_use_case.handle(summarizer_job=summarizer_job_dto)

                if result.advance_cursor:
                    self._chat_summary_state.last_chat_summary_time = occurred_at

                if result.summary is not None:
                    self._chat_summary_state.current_stream_summaries.append(result.summary)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                await asyncio.sleep(self._INTERVAL_DEFAULT)
