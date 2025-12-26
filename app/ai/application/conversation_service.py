from app.ai.domain.message_repository import AIMessageRepository
from app.ai.domain.models import AIMessage


class ConversationService:
    def __init__(self, message_repo: AIMessageRepository):
        self._message_repo = message_repo

    def get_last_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        return self._message_repo.get_last_messages(channel_name, system_prompt)

    def save_conversation_to_db(self, channel_name: str, user_message: str, ai_message: str) -> None:
        self._message_repo.add_messages_to_db(channel_name, user_message, ai_message)




