from datetime import UTC, datetime, timedelta
from random import randint

from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.joke.application.model.post_joke import PostJokeDTO
from app.joke.application.uow.joke_uow import JokeUnitOfWorkFactory
from app.joke.domain.model.configuration import JokesConfiguration
from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from core.types import SessionFactory


class HandlePostJokeUseCase:
    def __init__(
        self,
        user_cache: ViewerCachePort,
        platform_repository: PlatformRepository,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        joke_uow: JokeUnitOfWorkFactory,
        db_ro_session: SessionFactory,
    ):
        self._user_cache = user_cache
        self._platform_repository = platform_repository
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._joke_uow = joke_uow
        self._db_ro_session = db_ro_session

    async def handle(self, post_joke: PostJokeDTO) -> str | None:
        with self._joke_uow.create(read_only=True) as uow:
            configuration = await uow.jokes_configuration_repository.get_current_configuration(post_joke.channel_name)

        if not configuration.is_enabled:
            return None

        now = datetime.now(UTC)
        next_joke_time = configuration.next_joke_time

        if next_joke_time is not None and now < next_joke_time:
            return None

        broadcaster_id = await self._user_cache.get_viewer_id(post_joke.channel_name)

        if not broadcaster_id:
            return None

        stream_info = await self._platform_repository.get_stream_info(post_joke.channel_name)

        if stream_info is None or not stream_info.game_name:
            return None

        prompt = f"Придумай анекдот, связанный с категорией трансляции: {stream_info.game_name}."
        with self._db_ro_session() as session:
            joke_text = await self._generate_response_use_case_factory.get(session).generate_response(prompt, post_joke.channel_name)

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
