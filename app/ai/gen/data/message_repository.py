from sqlalchemy import case
from sqlalchemy.orm import Session

from app.ai.gen.data.db.ai_message import AIMessage as AIDbMessage
from app.ai.gen.domain.conversation_repository import ConversationRepository
from app.ai.gen.domain.models import AIMessage, Role


class ConversationRepositoryImpl(ConversationRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_last_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        role_order = case((AIDbMessage.role == Role.USER, 2), (AIDbMessage.role == Role.ASSISTANT, 1), else_=3)

        messages = (
            self._db.query(AIDbMessage)
            .filter_by(channel_name=channel_name)
            .filter(AIDbMessage.role != Role.SYSTEM)
            .order_by(AIDbMessage.created_at.desc(), role_order)
            .limit(50)
            .all()
        )
        messages.reverse()
        ai_messages = [AIMessage(Role.SYSTEM, system_prompt)]

        for message in messages:
            ai_messages.append(AIMessage(message.role, message.content))
        return ai_messages

    def add_messages_to_db(self, channel_name: str, user_message: str, ai_message: str) -> None:
        user_message = AIDbMessage(channel_name=channel_name, role=Role.USER, content=user_message)
        ai_message = AIDbMessage(channel_name=channel_name, role=Role.ASSISTANT, content=ai_message)
        self._db.add(user_message)
        self._db.add(ai_message)
