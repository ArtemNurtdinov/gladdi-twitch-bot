from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.equipment.domain.equipment_service import EquipmentService
from app.stream.domain.stream_service import StreamService
from core.db import SessionLocal, db_ro_session


class BonusCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        stream_service_factory: Callable[[Session], StreamService],
        equipment_service_factory: Callable[[Session], EquipmentService],
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._stream_service: Callable[[Session], StreamService] = stream_service_factory
        self._equipment_service = equipment_service_factory
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.nick_provider = nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        bot_nick = self.nick_provider() or ""
        user_name = display_name.lower()

        with db_ro_session() as db:
            active_stream = self._stream_service(db).get_active_stream(channel_name)

        if not active_stream:
            result = f"🚫 @{display_name}, бонус доступен только во время стрима!"
        else:
            with SessionLocal.begin() as db:
                user_equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)
                bonus_result = self._economy_service(db).claim_daily_bonus(
                    active_stream.id, channel_name, user_name, user_equipment
                )
                if bonus_result.success:
                    if bonus_result.bonus_message:
                        result = (
                            f"🎁 @{display_name} получил бонус {bonus_result.bonus_amount} монет! "
                            f"Баланс: {bonus_result.user_balance.balance} монет. {bonus_result.bonus_message}"
                        )
                    else:
                        result = (
                            f"🎁 @{display_name} получил бонус {bonus_result.bonus_amount} монет! "
                            f"Баланс: {bonus_result.user_balance.balance} монет"
                        )
                else:
                    if bonus_result.failure_reason == "already_claimed":
                        result = f"⏰ @{display_name}, бонус уже получен на этом стриме!"
                    elif bonus_result.failure_reason == "error":
                        result = f"❌ @{display_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                    else:
                        result = f"❌ @{display_name}, бонус недоступен!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        await self.post_message_fn(result, ctx)
