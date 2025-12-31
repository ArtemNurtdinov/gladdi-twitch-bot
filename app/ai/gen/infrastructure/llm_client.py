import httpx

from app.ai.gen.domain.llm_client import LLMClient
from app.ai.gen.domain.models import AIMessage
from core.config import config


class LLMClientImpl(LLMClient):
    _LLMBOX_API_DOMAIN = config.llmbox.host

    async def generate_ai_response(self, user_messages: list[AIMessage]) -> str:
        messages = [{"role": message.role.value, "content": message.content} for message in user_messages]
        payload = {"messages": messages, "assistant": "chat_gpt"}
        api_url = f"{self._LLMBOX_API_DOMAIN}/generate-ai-response"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(api_url, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            return response_data["assistant_message"]

        raise Exception(f"Ошибка запроса: {response.status_code} - {response.text}")
