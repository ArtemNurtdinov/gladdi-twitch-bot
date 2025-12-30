from datetime import timedelta
from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.stream.domain.stream_service import StreamService
from app.twitch.application.background.chat_summary.model import SummarizerJobDTO
from core.provider import Provider


class HandleChatSummarizerUseCase:

    def __init__(
        self,
        stream_service_provider: Provider[StreamService],
        chat_use_case_provider: Provider[ChatUseCase],
        chat_response_use_case: ChatResponseUseCase,
    ):
        self._stream_service_provider = stream_service_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._chat_response_use_case = chat_response_use_case

    async def handle(
        self,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        summarizer_job: SummarizerJobDTO,
    ) -> Optional[str]:
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(summarizer_job.channel_name)
        if not active_stream:
            return None

        since = summarizer_job.occurred_at - timedelta(minutes=summarizer_job.interval_minutes)
        with db_readonly_session_provider() as db:
            messages = self._chat_use_case_provider.get(db).get_last_chat_messages_since(summarizer_job.channel_name, since)

        if not messages:
            return None

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
        prompt = (
            f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
            f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
        )
        result = await self._chat_response_use_case.generate_response(prompt, summarizer_job.channel_name)
        return result
