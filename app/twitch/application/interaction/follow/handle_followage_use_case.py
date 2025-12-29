from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.domain.prompt_service import PromptService
from app.twitch.application.interaction.follow.dto import FollowageDTO
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.ai.gen.domain.conversation_service_provider import ConversationServiceProvider
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class HandleFollowageUseCase:

    def __init__(
        self,
        chat_use_case_provider: ChatUseCaseProvider,
        conversation_service_provider: ConversationServiceProvider,
        twitch_api_service: TwitchApiService,
        prompt_service: PromptService,
        chat_response_use_case: ChatResponseUseCase,
    ):
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._twitch_api_service = twitch_api_service
        self._prompt_service = prompt_service
        self._chat_response_use_case = chat_response_use_case

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        followage_dto: FollowageDTO,
    ) -> str:
        broadcaster = await self._twitch_api_service.get_user_by_login(followage_dto.channel_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id

        if not broadcaster_id:
            result = f"@{followage_dto.display_name}, произошла ошибка при получении информации о канале {followage_dto.channel_name}."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=followage_dto.channel_name,
                    user_name=followage_dto.bot_nick.lower(),
                    content=result,
                    current_time=followage_dto.occurred_at
                )
            return result

        follow_info = await self._twitch_api_service.get_user_followage(broadcaster_id, followage_dto.user_id)

        if follow_info:
            follow_dt = datetime.fromisoformat(follow_info.followed_at.replace("Z", "+00:00"))
            follow_duration = followage_dto.occurred_at - follow_dt

            days = follow_duration.days
            hours, remainder = divmod(follow_duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            prompt = (
                f"@{followage_dto.display_name} отслеживает канал {followage_dto.channel_name} уже {days} дней, {hours} часов и "
                f"{minutes} минут. Сообщи ему об этом как-нибудь оригинально."
            )
            result = await self._chat_response_use_case.generate_response(prompt, followage_dto.channel_name)

            with db_session_provider() as db:
                self._conversation_service_provider.get(db).save_conversation_to_db(
                    channel_name=followage_dto.channel_name,
                    user_message=prompt,
                    ai_message=result
                )
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=followage_dto.channel_name,
                    user_name=followage_dto.bot_nick.lower(),
                    content=result,
                    current_time=followage_dto.occurred_at,
                )
            return result

        result = f"@{followage_dto.display_name}, вы не отслеживаете канал {followage_dto.channel_name}."
        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=followage_dto.channel_name,
                user_name=followage_dto.bot_nick.lower(),
                content=result,
                current_time=followage_dto.occurred_at,
            )
        return result
