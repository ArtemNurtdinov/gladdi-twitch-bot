from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.ai.gen.conversation.domain.models import AIMessage, Role


class ConversationService:
    def __init__(self, message_repo: ConversationRepository):
        self._message_repo = message_repo

    def get_last_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        last_messages = self._message_repo.get_last_messages(channel_name)
        last_messages.reverse()
        ai_messages: list[AIMessage] = [AIMessage(role=Role.SYSTEM, content=system_prompt)] + [
            AIMessage(role=message.role, content=message.content) for message in last_messages
        ]
        return ai_messages

    def save_conversation_to_db(self, channel_name: str, user_message: str, ai_message: str) -> None:
        self._message_repo.add_messages_to_db(channel_name, user_message, ai_message)
