from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase


class ChatUseCaseProvider:

    def __init__(self, _chat_use_case_factory: Callable[[Session], ChatUseCase]):
        self._chat_use_case_factory = _chat_use_case_factory

    def get(self, db: Session) -> ChatUseCase:
        return self._chat_use_case_factory(db)