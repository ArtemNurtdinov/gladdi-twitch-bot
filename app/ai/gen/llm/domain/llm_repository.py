from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage


class LLMRepository:
    async def generate_ai_response(self, user_messages: list[AIMessage]) -> AIAssistantResponse: ...
