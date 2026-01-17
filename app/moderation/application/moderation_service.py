import logging

from app.moderation.application.chat_moderation_port import ChatModerationPort
from app.moderation.application.moderation_port import ModerationPort
from app.user.application.user_cache_port import UserCachePort

logger = logging.getLogger(__name__)


class ModerationService(ChatModerationPort):
    def __init__(self, moderation_port: ModerationPort, user_cache: UserCachePort):
        self._moderation_port = moderation_port
        self._user_cache = user_cache

    async def timeout_user(self, channel_name: str, moderator_name: str, username: str, duration_seconds: int, reason: str) -> bool:
        try:
            user_id = await self._user_cache.get_user_id(username)
            broadcaster_id = await self._user_cache.get_user_id(channel_name)
            moderator_id = await self._user_cache.get_user_id(moderator_name)

            if not user_id or not broadcaster_id or not moderator_id:
                logger.error("Не удалось получить user_id, broadcaster_id или moderator_id")
                return False

            return await self._moderation_port.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
        except Exception as e:
            logger.error(f"Ошибка при попытке дать таймаут пользователю {username}: {e}")
            return False
