from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.equipment.application.model import EquipmentDTO
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from core.provider import Provider


class HandleEquipmentUseCase:
    def __init__(
        self, get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase], chat_use_case_provider: Provider[ChatUseCase]
    ):
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        dto: EquipmentDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            equipment = self._get_user_equipment_use_case_provider.get(db).get_user_equipment(
                channel_name=dto.channel_name, user_name=dto.user_name
            )

        if not equipment:
            result = f"@{dto.display_name}, у вас нет активной экипировки. Загляните в {dto.command_prefix}{dto.command_shop}!"
        else:
            lines = [f"Экипировка @{dto.display_name}:"]
            for item in equipment:
                expires_date = item.expires_at.strftime("%d.%m.%Y")
                lines.append(f" {item.shop_item.emoji} {item.shop_item.name} до {expires_date}")
            result = "\n".join(lines)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick,
                content=result,
                current_time=dto.occurred_at,
            )

        return result
