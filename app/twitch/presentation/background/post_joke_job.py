import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable, Any

from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from core.db import SessionLocal
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class PostJokeJob:
    name = "post_joke"

    def __init__(
        self,
        channel_name: str,
        joke_service: Any,
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
        generate_response_in_chat: Callable[[str, str], str],
        ai_conversation_use_case_factory: Callable[[Any], Any],
        chat_use_case_factory: Callable[[Any], Any],
        send_channel_message: Callable[[str, str], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
    ):
        self._channel_name = channel_name
        self._joke_service = joke_service
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._generate_response_in_chat = generate_response_in_chat
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._chat_use_case_factory = chat_use_case_factory
        self._send_channel_message = send_channel_message
        self._bot_nick_provider = bot_nick_provider

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await asyncio.sleep(30)

                if not self._joke_service.should_generate_jokes():
                    continue

                broadcaster_id = await self._user_cache.get_user_id(self._channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {self._channel_name} для генерации анекдота")
                    continue

                stream_info = await self._twitch_api_service.get_stream_info(broadcaster_id)
                prompt = f"Придумай анекдот, связанной с категорией трансляции: {stream_info.game_name}."
                result = self._generate_response_in_chat(prompt, self._channel_name)
                with SessionLocal.begin() as db:
                    self._ai_conversation_use_case_factory(db).save_conversation_to_db(self._channel_name, prompt, result)
                    self._chat_use_case_factory(db).save_chat_message(
                        channel_name=self._channel_name,
                        user_name=self._bot_nick_provider().lower(),
                        content=result,
                        current_time=datetime.utcnow()
                    )
                await self._send_channel_message(self._channel_name, result)
                self._joke_service.mark_joke_generated()
            except asyncio.CancelledError:
                logger.info("PostJokeJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в PostJokeJob: {e}")
                await asyncio.sleep(60)
