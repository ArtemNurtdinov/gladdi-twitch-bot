from datetime import timedelta
from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.twitch.application.background.chat_summary.dto import ChatSummarizerDTO
from app.twitch.application.shared import ChatResponder, StreamServiceProvider


class HandleChatSummarizerUseCase:

    def __init__(
        self,
        stream_service_provider: StreamServiceProvider,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        chat_responder: ChatResponder,
    ):
        self._stream_service_provider = stream_service_provider
        self._chat_use_case_factory = chat_use_case_factory
        self._chat_responder = chat_responder

    async def handle(
        self,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        chat_summarizer: ChatSummarizerDTO,
    ) -> Optional[str]:
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(chat_summarizer.channel_name)
        if not active_stream:
            return None

        since = chat_summarizer.occurred_at - timedelta(minutes=chat_summarizer.interval_minutes)
        with db_readonly_session_provider() as db:
            messages = self._chat_use_case_factory(db).get_last_chat_messages_since(chat_summarizer.channel_name, since)

        if not messages:
            return None

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
        prompt = (
            f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
            f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
        )
        result = self._chat_responder.generate_response(prompt, chat_summarizer.channel_name)
        return result


