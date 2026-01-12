from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.conversation.infrastructure.db.ai_message import AIMessage as AIDbMessage


class ConversationRepositoryImpl(ConversationRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_last_messages(self, channel_name: str) -> list[AIMessage]:
        role_order = case((AIDbMessage.role == Role.USER, 2), (AIDbMessage.role == Role.ASSISTANT, 1), else_=3)
        stmt = (
            select(AIDbMessage)
            .where(AIDbMessage.channel_name == channel_name)
            .where(AIDbMessage.role != Role.SYSTEM)
            .order_by(AIDbMessage.created_at.desc(), role_order)
            .limit(50)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [AIMessage(r.role, r.content) for r in rows]

    def add_messages_to_db(self, channel_name: str, user_message: str, ai_message: str) -> None:
        user_message = AIDbMessage(channel_name=channel_name, role=Role.USER, content=user_message)
        ai_message = AIDbMessage(channel_name=channel_name, role=Role.ASSISTANT, content=ai_message)
        self._db.add(user_message)
        self._db.add(ai_message)
