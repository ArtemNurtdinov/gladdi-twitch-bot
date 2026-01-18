from collections.abc import Awaitable, Callable
from datetime import datetime

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
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
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

        result = await self._handle_equipment_use_case.handle(dto=dto)

        await self.post_message_fn(result, chat_ctx)
