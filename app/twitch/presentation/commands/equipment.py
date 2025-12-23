from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.equipment.domain.equipment_service import EquipmentService
from core.db import SessionLocal, db_ro_session


class EquipmentCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        command_shop: str,
        equipment_service_factory: Callable[[Session], EquipmentService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._equipment_service = equipment_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        user_name = display_name.lower()
        bot_nick = self.bot_nick_provider().lower()

        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)

        if not equipment:
            result = f"@{display_name}, у вас нет активной экипировки. Загляните в {self.command_prefix}{self.command_shop}!"
        else:
            result = f"Экипировка @{display_name}:\n"
            for item in equipment:
                expires_date = item.expires_at.strftime('%d.%m.%Y')
                result += f"{item.shop_item.emoji} {item.shop_item.name} до {expires_date}\n"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())

        await self.post_message_fn(result, ctx)
