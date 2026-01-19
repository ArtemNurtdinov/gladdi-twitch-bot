from datetime import timedelta

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.chat.application.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.chat.application.model import SummarizerJobDTO


class HandleChatSummarizerUseCase:
    def __init__(
        self,
        unit_of_work_factory: ChatSummarizerUnitOfWorkFactory,
        chat_response_use_case: ChatResponseUseCase,
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._chat_response_use_case = chat_response_use_case

    async def handle(
        self,
        summarizer_job: SummarizerJobDTO,
    ) -> str | None:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(summarizer_job.channel_name)
            if not active_stream:
                return None

            since = summarizer_job.occurred_at - timedelta(minutes=summarizer_job.interval_minutes)
            messages = uow.chat_use_case.get_last_chat_messages_since(summarizer_job.channel_name, since)

        if not messages:
            return None

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
        prompt = (
            f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
            f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
        )
        result = await self._chat_response_use_case.generate_response(prompt, summarizer_job.channel_name)
        return result
