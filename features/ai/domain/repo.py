from typing import Generic, Protocol, TypeVar

from features.ai.domain.models import AIMessage, Intent

DB = TypeVar("DB")


class AIRepository(Protocol, Generic[DB]):

    def generate_ai_response(self, user_messages: list[AIMessage]) -> str:
        ...

    def extract_intent_from_text(self, text: str) -> Intent:
        ...

    def validate_intent_via_llm(self, detected_intent: Intent, text: str) -> Intent:
        ...

    def get_last_messages(self, db: DB, channel_name: str, system_prompt: str) -> list[AIMessage]:
        ...

    def add_messages_to_db(self, db: DB, channel_name: str, user_message: str, ai_message: str):
        ...
