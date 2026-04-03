import asyncio
from datetime import datetime

from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.application.model.summarizer_job import SummarizerJobDTO
from app.chat.application.usecase.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.core.logger.domain.logger import Logger
from core.background.task_runner import BackgroundTaskRunner
from core.background.tasks import BackgroundJob


class ChatSummarizerJob(BackgroundJob):
    name = "summarize_chat"
    _INTERVAL_DEFAULT = 120

    def __init__(
        self,
        channel_name: str,
        handle_chat_summarizer_use_case: HandleChatSummarizerUseCase,
        chat_summary_state: ChatSummaryState,
        logger: Logger,
    ):
        self._channel_name = channel_name
        self._handle_chat_summarizer_use_case = handle_chat_summarizer_use_case
        self._chat_summary_state = chat_summary_state
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(self._INTERVAL_DEFAULT)

                summarizer_job_dto = SummarizerJobDTO(channel_name=self._channel_name, occurred_at=datetime.utcnow(), interval_minutes=20)

                result = await self._handle_chat_summarizer_use_case.handle(summarizer_job=summarizer_job_dto)
                if result is None:
                    continue

                self._chat_summary_state.current_stream_summaries.append(result)
                self._chat_summary_state.last_chat_summary_time = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("error while running", e)
                await asyncio.sleep(self._INTERVAL_DEFAULT)
