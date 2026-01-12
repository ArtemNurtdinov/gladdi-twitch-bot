from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.equipment.application.model import EquipmentDTO
from core.chat.interfaces import ChatContext


class EquipmentCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        command_shop: str,
        handle_equipment_use_case: HandleEquipmentUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.command_name = command_name
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        dto = EquipmentDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            command_name=self.command_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            command_shop=self.command_shop,
        )

        result = await self._handle_equipment_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, chat_ctx)
