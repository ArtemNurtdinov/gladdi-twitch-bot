from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.equipment.application.get_user_equipment_use_case_provider import GetUserEquipmentUseCaseProvider
from app.stream.application.stream_service_provider import StreamServiceProvider
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.economy.application.economy_service_provider import EconomyServiceProvider
from app.twitch.application.interaction.dto import ChatContextDTO


class HandleBonusUseCase:

    def __init__(
        self,
        stream_service_provider: StreamServiceProvider,
        get_user_equipment_use_case_provider: GetUserEquipmentUseCaseProvider,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
    ):
        self._stream_service_provider = stream_service_provider
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        chat_context_dto: ChatContextDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(chat_context_dto.channel_name)

        if not active_stream:
            result = f"🚫 @{chat_context_dto.display_name}, бонус доступен только во время стрима!"
        else:
            with db_session_provider() as db:
                user_equipment = self._get_user_equipment_use_case_provider.get(db).get_user_equipment(
                    channel_name=chat_context_dto.channel_name,
                    user_name=chat_context_dto.user_name
                )
                bonus_result = self._economy_service_provider.get(db).claim_daily_bonus(
                    active_stream_id=active_stream.id,
                    channel_name=chat_context_dto.channel_name,
                    user_name=chat_context_dto.user_name,
                    user_equipment=user_equipment
                )
                if bonus_result.success:
                    if bonus_result.bonus_message:
                        result = f"🎁 @{chat_context_dto.display_name} получил бонус {bonus_result.bonus_amount} монет! {bonus_result.bonus_message}"
                    else:
                        result =  f"🎁 @{chat_context_dto.display_name} получил бонус {bonus_result.bonus_amount} монет!"
                else:
                    if bonus_result.failure_reason == "already_claimed":
                        result = f"⏰ @{chat_context_dto.display_name}, бонус уже получен на этом стриме!"
                    elif bonus_result.failure_reason == "error":
                        result = f"❌ @{chat_context_dto.display_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                    else:
                        result = f"❌ @{chat_context_dto.display_name}, бонус недоступен!"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=chat_context_dto.channel_name,
                user_name=chat_context_dto.bot_nick,
                content=result,
                current_time=chat_context_dto.occurred_at,
            )

        return result
