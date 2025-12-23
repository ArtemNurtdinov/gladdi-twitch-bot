import asyncio
import logging
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.equipment.domain.equipment_service import EquipmentService
from app.stream.domain.stream_service import StreamService
from core.db import SessionLocal, db_ro_session

logger = logging.getLogger(__name__)


class BonusCommandHandler:

    def __init__(
        self,
        stream_service_factory: Callable[[Session], StreamService],
        equipment_service_factory: Callable[[Session], EquipmentService],
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_name: str,
        prefix: str,
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._stream_service: Callable[[Session], StreamService] = stream_service_factory
        self._equipment_service = equipment_service_factory
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.prefix = prefix
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_name} от пользователя {user_name}")

        with db_ro_session() as db:
            active_stream = self._stream_service(db).get_active_stream(channel_name)

        if not active_stream:
            result = f"🚫 @{user_name}, бонус доступен только во время стрима!"
        else:
            with SessionLocal.begin() as db:
                user_equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name.lower())
                bonus_result = self._economy_service(db).claim_daily_bonus(
                    active_stream.id, channel_name, user_name.lower(), user_equipment
                )
                if bonus_result.success:
                    if bonus_result.bonus_message:
                        result = (
                            f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! "
                            f"Баланс: {bonus_result.user_balance.balance} монет. {bonus_result.bonus_message}"
                        )
                    else:
                        result = (
                            f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! "
                            f"Баланс: {bonus_result.user_balance.balance} монет"
                        )
                else:
                    if bonus_result.failure_reason == "already_claimed":
                        result = f"⏰ @{user_name}, бонус уже получен на этом стриме!"
                    elif bonus_result.failure_reason == "error":
                        result = f"❌ @{user_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                    else:
                        result = f"❌ @{user_name}, бонус недоступен!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

