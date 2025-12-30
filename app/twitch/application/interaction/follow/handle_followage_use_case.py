from typing import Optional

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.domain.conversation_service import ConversationService
from app.ai.gen.domain.prompt_service import PromptService
from app.chat.application.chat_use_case import ChatUseCase
from app.twitch.application.interaction.follow.get_followage_use_case import GetFollowageUseCase
from app.twitch.application.interaction.follow.model import FollowageDTO, FollowageInfo
from app.twitch.application.interaction.follow.uow import FollowAgeUnitOfWorkRoFactory, FollowAgeUnitOfWorkRwFactory
from core.provider import Provider


class HandleFollowAgeUseCase:

    def __init__(
        self,
        chat_use_case_provider: Provider[ChatUseCase],
        conversation_service_provider: Provider[ConversationService],
        get_followage_use_case: GetFollowageUseCase,
        prompt_service: PromptService,
        chat_response_use_case: ChatResponseUseCase,
        unit_of_work_ro_factory: FollowAgeUnitOfWorkRoFactory,
        unit_of_work_rw_factory: FollowAgeUnitOfWorkRwFactory,
        system_prompt: str
    ):
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._get_followage_use_case = get_followage_use_case
        self._prompt_service = prompt_service
        self._chat_response_use_case = chat_response_use_case
        self._unit_of_work_ro_factory = unit_of_work_ro_factory
        self._unit_of_work_rw_factory = unit_of_work_rw_factory
        self._system_prompt = system_prompt

    async def handle(self, command_follow_age: FollowageDTO) -> Optional[str]:
        channel_name = command_follow_age.channel_name

        follow_info: Optional[FollowageInfo] = await self._get_followage_use_case.get_followage(
            channel_login=channel_name,
            user_id=command_follow_age.user_id,
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

        follow_duration = command_follow_age.occurred_at - follow_info.followed_at

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
