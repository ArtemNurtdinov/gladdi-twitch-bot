import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.chat.application.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.application.model import ChatSummaryState, SummarizerJobDTO
from core.background_task_runner import BackgroundTaskRunner


class ChatSummarizerJob:
    name = "summarize_chat"

    def __init__(
        self,
        channel_name: str,
        handle_chat_summarizer_use_case: HandleChatSummarizerUseCase,
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        chat_summary_state: ChatSummaryState,
    ):
        self._channel_name = channel_name
        self._handle_chat_summarizer_use_case = handle_chat_summarizer_use_case
        self._db_readonly_session_provider = db_readonly_session_provider
        self._chat_summary_state = chat_summary_state

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(20 * 60)

                summarizer_job_dto = SummarizerJobDTO(channel_name=self._channel_name, occurred_at=datetime.utcnow(), interval_minutes=20)

                result = await self._handle_chat_summarizer_use_case.handle(
                    db_readonly_session_provider=self._db_readonly_session_provider, summarizer_job=summarizer_job_dto
                )
                if result is None:
                    continue

                self._chat_summary_state.current_stream_summaries.append(result)
                self._chat_summary_state.last_chat_summary_time = datetime.utcnow()
            except asyncio.CancelledError:
                break
            except Exception:
                pass
