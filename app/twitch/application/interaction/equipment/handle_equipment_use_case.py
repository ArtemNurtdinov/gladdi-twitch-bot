from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.equipment.dto import EquipmentDTO
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.equipment_service_provider import EquipmentServiceProvider


class HandleEquipmentUseCase:

    def __init__(
        self,
        equipment_service_provider: EquipmentServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider
    ):
        self._equipment_service_provider = equipment_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: EquipmentDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            equipment = self._equipment_service_provider.get(db).get_user_equipment(dto.channel_name, dto.user_name)

        if not equipment:
            result = (
                f"@{dto.display_name}, у вас нет активной экипировки. "
                f"Загляните в {dto.command_prefix}{dto.command_shop}!"
            )
        else:
            lines = [f"Экипировка @{dto.display_name}:"]
            for item in equipment:
                expires_date = item.expires_at.strftime("%d.%m.%Y")
                lines.append(f"{item.shop_item.emoji} {item.shop_item.name} до {expires_date}")
            result = "\n".join(lines)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick,
                content=result,
                current_time=dto.occurred_at,
            )

        return result
