from datetime import UTC, datetime, timedelta
from random import randint

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.joke.application.model.post_joke import PostJokeDTO
from app.joke.application.uow.joke_uow import JokeUnitOfWorkFactory
from app.joke.domain.model.configuration import JokesConfiguration
from app.platform.domain.repository import PlatformRepository
from app.user.application.ports.user_cache_port import UserCachePort


class HandlePostJokeUseCase:
    def __init__(
        self,
        user_cache: UserCachePort,
        platform_repository: PlatformRepository,
        chat_response_use_case: GenerateResponseUseCase,
        joke_uow: JokeUnitOfWorkFactory,
    ):
        self._user_cache = user_cache
        self._platform_repository = platform_repository
        self._chat_response_use_case = chat_response_use_case
        self._joke_uow = joke_uow

    async def handle(self, post_joke: PostJokeDTO) -> str | None:
        with self._joke_uow.create(read_only=True) as uow:
            configuration = await uow.jokes_configuration_repository.get_current_configuration(post_joke.channel_name)

        if not configuration.is_enabled:
            return None

        if not configuration.next_joke_time:
            return None

        now = datetime.now(UTC)
        next_joke_time = configuration.next_joke_time

        if now < next_joke_time:
            return None

        broadcaster_id = await self._user_cache.get_user_id(post_joke.channel_name)

        if not broadcaster_id:
            return None

        stream_info = await self._platform_repository.get_stream_info(post_joke.channel_name)

        if not stream_info or not stream_info.game_name:
            return None

        prompt = f"Придумай анекдот, связанный с категорией трансляции: {stream_info.game_name}."
        joke_text = await self._chat_response_use_case.generate_response(prompt, post_joke.channel_name)

        with self._joke_uow.create() as uow:
            uow.conversation_service.save_conversation_to_db(channel_name=post_joke.channel_name, user_message=prompt, ai_message=joke_text)
            uow.chat_use_case.save_chat_message(
                channel_name=post_joke.channel_name,
                user_name=post_joke.bot_nick,
                content=joke_text,
                current_time=post_joke.occurred_at,
            )

        now = datetime.now(UTC)
        interval_minutes = randint(configuration.interval_min, configuration.interval_max)
        next_joke_time = now + timedelta(minutes=interval_minutes)

        configuration_updated = JokesConfiguration(
            channel_name=configuration.channel_name,
            interval_min=configuration.interval_min,
            interval_max=configuration.interval_max,
            last_joke_time=now,
            next_joke_time=next_joke_time,
            is_enabled=configuration.is_enabled,
        )

        with self._joke_uow.create() as uow:
            await uow.jokes_configuration_repository.save_configuration(configuration_updated)

        return joke_text
