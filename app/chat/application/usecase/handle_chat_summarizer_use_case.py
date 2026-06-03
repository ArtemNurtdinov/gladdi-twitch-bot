from datetime import timedelta

from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.chat.application.model.summarizer_job import SummarizerJobDTO
from app.chat.application.uow.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from core.types import SessionFactory


class HandleChatSummarizerUseCase:
    _INTERVAL_MINUTES: int = 20

    def __init__(
        self,
        chat_summarizer_uow: ChatSummarizerUnitOfWorkFactory,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        session_ro_factory: SessionFactory,
    ):
        self._chat_summarizer_uow = chat_summarizer_uow
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._session_ro = session_ro_factory

    async def handle(self, summarizer_job: SummarizerJobDTO) -> str | None:
        with self._chat_summarizer_uow.create(read_only=True) as uow:
            active_stream = uow.stream_repository.get_active_stream(summarizer_job.channel_name)
            if not active_stream:
                return None

            since = summarizer_job.occurred_at - timedelta(minutes=self._INTERVAL_MINUTES)
            messages = uow.chat_use_case.get_last_chat_messages_since(summarizer_job.channel_name, since)

        if not messages:
            return None

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
        prompt = (
            f"Основываясь на сообщения в чате, подведи краткий итог общения в виде тезисов, без нумерации. Для отчёта. "
            f"Зафиксируй наиболее смешные и наиболее важные моменты, которые обсуждались в чате. Желательно с никнеймами."
            f"Вот сообщения: {chat_text}"
        )
        with self._session_ro() as session:
            result = await self._generate_response_use_case_factory.get(session).generate_response(prompt, summarizer_job.channel_name)
        return result
