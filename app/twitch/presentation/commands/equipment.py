import asyncio
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.equipment.domain.equipment_service import EquipmentService
from core.db import SessionLocal, db_ro_session


class EquipmentCommandHandler:

    def __init__(
        self,
        equipment_service_factory: Callable[[Session], EquipmentService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_name: str,
        command_shop: str,
        prefix: str,
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._equipment_service = equipment_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.command_shop = command_shop
        self.prefix = prefix
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        user_name = display_name.lower()
        bot_nick = self.nick_provider() or ""

        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)

        if not equipment:
            result = f"@{display_name}, у вас нет активной экипировки. Загляните в {self.prefix}{self.command_shop}!"
        else:
            result = f"Экипировка @{display_name}:\n"
            for item in equipment:
                expires_date = item.expires_at.strftime('%d.%m.%Y')
                result += f"{item.shop_item.emoji} {item.shop_item.name} до {expires_date}\n"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)
