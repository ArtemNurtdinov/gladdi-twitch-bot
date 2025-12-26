from typing import Callable, ContextManager, Optional

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.joke.domain.joke_service import JokeService
from app.twitch.application.background.post_joke.dto import PostJokeDTO
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class HandlePostJokeUseCase:

    def __init__(
        self,
        joke_service: JokeService,
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
        generate_response_fn: Callable[[str, str], str],
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
    ):
        self._joke_service = joke_service
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._generate_response_fn = generate_response_fn
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._chat_use_case_factory = chat_use_case_factory

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
        result = self._generate_response_fn(prompt, post_joke.channel_name)

        with db_session_provider() as db:
            self._ai_conversation_use_case_factory(db).save_conversation_to_db(post_joke.channel_name, prompt, result)
            self._chat_use_case_factory(db).save_chat_message(
                channel_name=post_joke.channel_name,
                user_name=post_joke.bot_nick,
                content=result,
                current_time=post_joke.occurred_at,
            )

        self._joke_service.mark_joke_generated()
        return result
