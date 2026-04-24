from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.equipment.application.model import EquipmentDTO


class EquipmentCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_shop: str,
        handle_equipment_use_case: HandleEquipmentUseCase,
    ):
        self._handle_equipment_use_case = handle_equipment_use_case
        self.command_shop = command_shop
        self.command_prefix = command_prefix
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        equipment = EquipmentDTO(
            command_prefix=self.command_prefix,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            command_shop=self.command_shop,
            message=message,
        )

        return await self._handle_equipment_use_case.handle(equipment_command=equipment)
