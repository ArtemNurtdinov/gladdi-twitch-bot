from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.ai.application.chat_responder import ChatResponder
from app.joke.domain.joke_service import JokeService
from app.twitch.application.background.post_joke.dto import PostJokeDTO
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.ai.application.conversation_service_provider import ConversationServiceProvider
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class HandlePostJokeUseCase:

    def __init__(
        self,
        joke_service: JokeService,
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
        chat_responder: ChatResponder,
        conversation_service_provider: ConversationServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider
    ):
        self._joke_service = joke_service
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._chat_responder = chat_responder
        self._conversation_service_provider = conversation_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        post_joke: PostJokeDTO,
    ) -> Optional[str]:
        if not self._joke_service.should_generate_jokes():
            return None

        broadcaster_id = await self._user_cache.get_user_id(post_joke.channel_name)

        if not broadcaster_id:
            return None

        stream_info = await self._twitch_api_service.get_stream_info(broadcaster_id)
        game_name = stream_info.game_name if stream_info else "стрима"
        prompt = f"Придумай анекдот, связанный с категорией трансляции: {game_name}."
        result = await self._chat_responder.generate_response(prompt, post_joke.channel_name)

        with db_session_provider() as db:
            self._conversation_service_provider.get(db).save_conversation_to_db(post_joke.channel_name, prompt, result)
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=post_joke.channel_name,
                user_name=post_joke.bot_nick,
                content=result,
                current_time=post_joke.occurred_at,
            )

        self._joke_service.mark_joke_generated()
        return result
