import httpx
from pydantic import ValidationError

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage, Usage
from app.ai.gen.llm.domain.llm_client_exceptions import LLMClientError, LLMResponseFormatError
from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from app.ai.gen.llm.infrastructure.llm_schemas import AIResponseSchema
from core.config import config


class LLMBoxClientPortImpl(LLMClientPort):
    _LLMBOX_API_DOMAIN = config.llmbox.host

    async def generate_ai_response(self, user_messages: list[AIMessage]) -> AIAssistantResponse:
        messages = [{"role": message.role.value, "content": message.content} for message in user_messages]
        payload = {"messages": messages, "assistant": "chat_gpt"}
        api_url = f"{self._LLMBOX_API_DOMAIN}/generate-ai-response"

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(api_url, json=payload)
        except httpx.RequestError as exc:
            raise LLMClientError(f"LLMBox недоступен: {exc}") from exc

        if response.status_code != 200:
            raise LLMClientError(f"LLMBox вернул {response.status_code}: {response.text}")

        try:
            response_data = response.json()
        except ValueError as exc:
            raise LLMResponseFormatError("LLMBox вернул некорректный JSON") from exc

        try:
            validated = AIResponseSchema.parse_obj(response_data)
        except ValidationError as exc:
            raise LLMResponseFormatError(f"LLMBox: формат ответа невалиден: {exc}") from exc

        usage_schema = validated.usage
        usage = Usage(
            prompt_tokens=int(usage_schema.prompt_tokens or 0),
            completion_tokens=int(usage_schema.completion_tokens or 0),
            total_tokens=int(usage_schema.total_tokens or 0),
        )

        return AIAssistantResponse(message=validated.assistant_message, usage=usage)
