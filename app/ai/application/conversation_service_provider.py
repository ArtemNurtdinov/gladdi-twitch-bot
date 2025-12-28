from typing import Callable

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService


class ConversationServiceProvider:

    def __init__(self, conversation_service_factory: Callable[[Session], ConversationService]):
        self._conversation_service_factory = conversation_service_factory

    def get(self, db: Session) -> ConversationService:
        return self._conversation_service_factory(db)
