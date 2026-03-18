from app.commands.equipment.application.equipment_uow import EquipmentUnitOfWorkFactory
from app.commands.equipment.application.model import EquipmentDTO


class HandleEquipmentUseCase:
    def __init__(self, unit_of_work_factory: EquipmentUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(self, equipment_command: EquipmentDTO) -> str:
        user_message = equipment_command.command_prefix + equipment_command.command_name
        with self._unit_of_work_factory.create(read_only=True) as uow:
            equipment = uow.get_user_equipment_use_case.get_user_equipment(
                channel_name=equipment_command.channel_name, user_name=equipment_command.user_name
            )

        if not equipment:
            result = f"@{equipment_command.display_name}, у вас нет активной экипировки. Загляните в {equipment_command.command_prefix}{equipment_command.command_shop}!"
        else:
            lines = [f"Экипировка @{equipment_command.display_name}:"]
            for item in equipment:
                expires_date = item.expires_at.strftime("%d.%m.%Y")
                lines.append(f" {item.shop_item.emoji} {item.shop_item.name} до {expires_date}")
            result = "\n".join(lines)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=equipment_command.channel_name,
                user_name=equipment_command.user_name,
                content=user_message,
                current_time=equipment_command.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=equipment_command.channel_name,
                user_name=equipment_command.bot_nick,
                content=result,
                current_time=equipment_command.occurred_at,
            )

        return result
