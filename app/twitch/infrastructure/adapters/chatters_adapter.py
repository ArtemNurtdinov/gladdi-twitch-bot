from __future__ import annotations

import logging

from pydantic import ValidationError

from app.twitch.infrastructure.api_client import StreamingApiClient
from app.twitch.infrastructure.api_common import handle_api_response
from app.twitch.infrastructure.twitch_api_models import ChattersResponse
from app.viewer.application.stream_chatters_port import StreamChattersPort

logger = logging.getLogger(__name__)


class ChattersApiAdapter(StreamChattersPort):
    def __init__(self, client: StreamingApiClient):
        self._client = client

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]:
        try:
            response = await self._client.get("/chat/chatters", params={"broadcaster_id": broadcaster_id, "moderator_id": moderator_id})
            data = await handle_api_response(response, f"get_stream_chatters({broadcaster_id})")
            try:
                parsed: ChattersResponse = ChattersResponse.model_validate(data)
            except ValidationError as e:
                logger.error(f"Валидация chatters для {broadcaster_id} не прошла: {e}")
                return []

            chatters = parsed.data
            return [ch.user_login for ch in chatters]
        except Exception as e:
            logger.error(f"Ошибка при получении списка зрителей: {e}")
            return []

