import httpx
from openai import APIConnectionError, APIStatusError, AsyncOpenAI
from openai.types.chat import ChatCompletionAssistantMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.ai.gen.conversation.domain.models import AIAssistantResponse, AIMessage, Role, Usage
from app.ai.gen.llm.domain.exceptions.llm_exceptions import LLMClientError


class OpenAIChatClient:
    def __init__(self, api_key: str, model: str, proxy_url: str | None = None):
        if not api_key or not model:
            raise ValueError("OpenAI model and api_key are required")
        self._model = model
        http_client = httpx.AsyncClient(proxies=proxy_url) if proxy_url else None
        self._client = AsyncOpenAI(api_key=api_key, http_client=http_client)

    async def generate(self, messages: list[AIMessage]) -> AIAssistantResponse:
        payload = [self._to_chat_message(message) for message in messages]
        try:
            completion = await self._client.chat.completions.create(model=self._model, messages=payload, reasoning_effort="none")
        except (APIConnectionError, APIStatusError) as exc:
            raise LLMClientError(f"OpenAI недоступен: {exc}") from exc

        content = completion.choices[0].message.content or ""
        usage = completion.usage
        return AIAssistantResponse(
            message=content,
            usage=Usage(
                prompt_tokens=int(usage.prompt_tokens if usage else 0),
                completion_tokens=int(usage.completion_tokens if usage else 0),
                total_tokens=int(usage.total_tokens if usage else 0),
            ),
        )

    @staticmethod
    def _to_chat_message(
        message: AIMessage,
    ) -> ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam:
        if message.role == Role.SYSTEM:
            return ChatCompletionSystemMessageParam(role="system", content=message.content)
        if message.role == Role.ASSISTANT:
            return ChatCompletionAssistantMessageParam(role="assistant", content=message.content)
        return ChatCompletionUserMessageParam(role="user", content=message.content)
