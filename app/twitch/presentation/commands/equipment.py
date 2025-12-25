from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.equipment.dto import EquipmentDTO
from app.twitch.application.interaction.equipment.handle_equipment_use_case import HandleEquipmentUseCase


class EquipmentCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        command_shop: str,
        handle_equipment_use_case: HandleEquipmentUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.command_name = command_name
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx):
        dto = EquipmentDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
            command_prefix=self.command_prefix,
            command_shop=self.command_shop,
        )

        result = await self._handle_equipment_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            dto=dto,
        )

        await self.post_message_fn(result, ctx)
