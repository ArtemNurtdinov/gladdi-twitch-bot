from __future__ import annotations

import logging

from app.moderation.application.moderation_port import ModerationPort
from app.twitch.infrastructure.api_client import StreamingApiClient

logger = logging.getLogger(__name__)


class ModerationApiAdapter(ModerationPort):
    def __init__(self, client: StreamingApiClient):
        self._client = client

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        response = await self._client.post(
            "/moderation/bans",
            params={"broadcaster_id": broadcaster_id, "moderator_id": moderator_id},
            headers={"Content-Type": "application/json"},
            json={"data": {"user_id": user_id, "duration": duration_seconds, "reason": reason}},
        )
        if response.status_code == 200:
            logger.info(f"Таймаут успешно применён для пользователя {user_id} на {duration_seconds} секунд за: {reason}")
            return True
        else:
            logger.error(f"Не удалось дать таймаут пользователю {user_id}. Status: {response.status_code}, Response: {response.text}")
            return False
