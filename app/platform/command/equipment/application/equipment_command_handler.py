from datetime import datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.equipment.application.model import EquipmentDTO


class EquipmentCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        command_shop: str,
        handle_equipment_use_case: HandleEquipmentUseCase,
        bot_name: str,
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
        self.command_name = command_name
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        equipment = EquipmentDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            command_name=self.command_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            command_shop=self.command_shop,
        )

        return await self._handle_equipment_use_case.handle(equipment_command=equipment)
