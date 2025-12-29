from datetime import datetime
from typing import Optional

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.domain.conversation_service_provider import ConversationServiceProvider
from app.ai.gen.domain.prompt_service import PromptService
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.interaction.follow.dto import FollowageDTO
from app.twitch.application.interaction.follow.uow import FollowAgeUnitOfWorkRoFactory, FollowAgeUnitOfWorkRwFactory
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class HandleFollowAgeUseCase:

    def __init__(
        self,
        chat_use_case_provider: ChatUseCaseProvider,
        conversation_service_provider: ConversationServiceProvider,
        twitch_api_service: TwitchApiService,
        prompt_service: PromptService,
        chat_response_use_case: ChatResponseUseCase,
        unit_of_work_ro_factory: FollowAgeUnitOfWorkRoFactory,
        unit_of_work_rw_factory: FollowAgeUnitOfWorkRwFactory,
        system_prompt: str
    ):
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._twitch_api_service = twitch_api_service
        self._prompt_service = prompt_service
        self._chat_response_use_case = chat_response_use_case
        self._unit_of_work_ro_factory = unit_of_work_ro_factory
        self._unit_of_work_rw_factory = unit_of_work_rw_factory
        self._system_prompt = system_prompt

    async def handle(self, command_follow_age: FollowageDTO) -> Optional[str]:
        channel_name = command_follow_age.channel_name

        broadcaster = await self._twitch_api_service.get_user_by_login(channel_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id

        if not broadcaster_id:
            return None

        follow_info = await self._twitch_api_service.get_user_followage(
            broadcaster_id=broadcaster_id,
            user_id=command_follow_age.user_id
        )

        if not follow_info:
            result = f"@{command_follow_age.display_name}, вы не отслеживаете канал {channel_name}."
            with self._unit_of_work_rw_factory.create() as uow:
                uow.chat.save_chat_message(
                    channel_name=channel_name,
                    user_name=command_follow_age.bot_nick.lower(),
                    content=result,
                    current_time=command_follow_age.occurred_at,
                )
            return result

        follow_dt = datetime.fromisoformat(follow_info.followed_at.replace("Z", "+00:00"))
        follow_dt_naive = follow_dt.replace(tzinfo=None)
        follow_duration = command_follow_age.occurred_at - follow_dt_naive

        days = follow_duration.days
        hours, remainder = divmod(follow_duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        prompt = (
            f"@{command_follow_age.display_name} отслеживает канал {channel_name} уже {days} дней, {hours} часов и "
            f"{minutes} минут. Сообщи ему об этом кратко и оригинально."
        )

        with self._unit_of_work_ro_factory.create() as uow:
            history = uow.conversation.get_last_messages(
                channel_name=command_follow_age.channel_name,
                system_prompt=self._system_prompt
            )

        assistant_message = await self._chat_response_use_case.generate_response_from_history(
            history=history,
            prompt=prompt
        )

        with self._unit_of_work_rw_factory.create() as uow:
            uow.conversation.save_conversation_to_db(
                channel_name=channel_name,
                user_message=prompt,
                ai_message=assistant_message
            )
            uow.chat.save_chat_message(
                channel_name=channel_name,
                user_name=command_follow_age.bot_nick.lower(),
                content=assistant_message,
                current_time=command_follow_age.occurred_at
            )
        return assistant_message
