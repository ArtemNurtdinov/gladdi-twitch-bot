from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.joke.application.model import PostJokeDTO
from app.joke.domain.joke_service import JokeService
from app.stream.application.stream_info_port import StreamInfoPort
from app.user.infrastructure.cache.user_cache_service import UserCacheService
from core.provider import Provider


class HandlePostJokeUseCase:
    def __init__(
        self,
        joke_service: JokeService,
        user_cache: UserCacheService,
        stream_info: StreamInfoPort,
        chat_response_use_case: ChatResponseUseCase,
        conversation_service_provider: Provider[ConversationService],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        self._joke_service = joke_service
        self._user_cache = user_cache
        self._stream_info = stream_info
        self._chat_response_use_case = chat_response_use_case
        self._conversation_service_provider = conversation_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        post_joke: PostJokeDTO,
    ) -> str | None:
        if not self._joke_service.should_generate_jokes():
            return None

        broadcaster_id = await self._user_cache.get_user_id(post_joke.channel_name)

        if not broadcaster_id:
            return None

        stream_info = await self._stream_info.get_stream_info(post_joke.channel_name)

        if not stream_info or not stream_info.game_name:
            return None

        prompt = f"Придумай анекдот, связанный с категорией трансляции: {stream_info.game_name}."
        joke_text = await self._chat_response_use_case.generate_response(prompt, post_joke.channel_name)

        with db_session_provider() as db:
            self._conversation_service_provider.get(db).save_conversation_to_db(
                channel_name=post_joke.channel_name, user_message=prompt, ai_message=joke_text
            )
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=post_joke.channel_name,
                user_name=post_joke.bot_nick,
                content=joke_text,
                current_time=post_joke.occurred_at,
            )

        self._joke_service.mark_joke_generated()
        return joke_text
