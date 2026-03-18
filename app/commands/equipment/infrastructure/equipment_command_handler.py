from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.equipment.application.equipment_command_handler import EquipmentCommandHandler
from app.commands.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.equipment.application.model import EquipmentDTO


class EquipmentCommandHandlerImpl(EquipmentCommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        command_shop: str,
        handle_equipment_use_case: HandleEquipmentUseCase,
        bot_name: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
        self.command_name = command_name
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self._bot_name = bot_name
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str):
        equipment = EquipmentDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            command_name=self.command_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            command_shop=self.command_shop,
        )

        result = await self._handle_equipment_use_case.handle(equipment_command=equipment)

        await self.post_message_fn(result)
