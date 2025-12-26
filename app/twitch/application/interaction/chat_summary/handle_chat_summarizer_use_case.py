from datetime import datetime, timedelta
from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.twitch.application.interaction.chat_summary.dto import ChatSummarizerDTO
from app.twitch.application.shared import StreamServiceProvider
from app.chat.application.chat_use_case import ChatUseCase


class HandleChatSummarizerUseCase:

    def __init__(
        self,
        stream_service_provider: StreamServiceProvider,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        generate_response_fn: Callable[[str, str], str],
    ):
        self._stream_service_provider = stream_service_provider
        self._chat_use_case_factory = chat_use_case_factory
        self._generate_response_fn = generate_response_fn

    async def handle(
        self,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: ChatSummarizerDTO,
    ) -> Optional[str]:
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(dto.channel_name)
        if not active_stream:
            return None

        since = dto.occurred_at - timedelta(minutes=dto.interval_minutes)
        with db_readonly_session_provider() as db:
            messages = self._chat_use_case_factory(db).get_last_chat_messages_since(dto.channel_name, since)

        if not messages:
            return None

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
        prompt = (
            f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
            f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
        )
        result = self._generate_response_fn(prompt, dto.channel_name)
        return result

