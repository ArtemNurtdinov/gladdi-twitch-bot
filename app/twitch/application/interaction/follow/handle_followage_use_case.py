from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.ai.application.prompt_service import PromptService
from app.chat.application.chat_use_case import ChatUseCase
from app.twitch.application.interaction.follow.dto import FollowageDTO
from app.twitch.application.shared import ChatResponder
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


class HandleFollowageUseCase:

    def __init__(
        self,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        twitch_api_service: TwitchApiService,
        prompt_service: PromptService,
        chat_responder: ChatResponder,
    ):
        self._chat_use_case_factory = chat_use_case_factory
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._twitch_api_service = twitch_api_service
        self._prompt_service = prompt_service
        self._chat_responder = chat_responder

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: FollowageDTO,
    ) -> str:
        broadcaster = await self._twitch_api_service.get_user_by_login(dto.channel_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id

        if not broadcaster_id:
            result = f"@{dto.display_name}, произошла ошибка при получении информации о канале {dto.channel_name}."
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=dto.bot_nick.lower(),
                    content=result,
                    current_time=dto.occurred_at,
                )
            return result

        follow_info = await self._twitch_api_service.get_user_followage(broadcaster_id, dto.user_id)

        if follow_info:
            follow_dt = datetime.fromisoformat(follow_info.followed_at.replace("Z", "+00:00"))
            follow_duration = dto.occurred_at - follow_dt

            days = follow_duration.days
            hours, remainder = divmod(follow_duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            prompt = (
                f"@{dto.display_name} отслеживает канал {dto.channel_name} уже {days} дней, {hours} часов и "
                f"{minutes} минут. Сообщи ему об этом как-нибудь оригинально."
            )
            result = self._chat_responder.generate_response(prompt, dto.channel_name)

            with db_session_provider() as db:
                self._ai_conversation_use_case_factory(db).save_conversation_to_db(
                    dto.channel_name, prompt, result
                )
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=dto.bot_nick.lower(),
                    content=result,
                    current_time=dto.occurred_at,
                )
            return result

        result = f"@{dto.display_name}, вы не отслеживаете канал {dto.channel_name}."
        with db_session_provider() as db:
            self._chat_use_case_factory(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick.lower(),
                content=result,
                current_time=dto.occurred_at,
            )
        return result

