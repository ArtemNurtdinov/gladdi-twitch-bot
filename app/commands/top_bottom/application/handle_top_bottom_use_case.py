from datetime import datetime, timedelta

from app.commands.top_bottom.application.model import BottomDTO, TopDTO
from app.commands.top_bottom.application.top_bottom_uow import TopBottomUnitOfWorkFactory


class HandleTopBottomUseCase:
    def __init__(self, unit_of_work_factory: TopBottomUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle_top(
        self,
        command_top: TopDTO,
    ) -> str:
        user_message = command_top.command_prefix + command_top.command_name
        with self._unit_of_work_factory.create(read_only=True) as uow:
            top_users = uow.economy_policy.get_top_users(command_top.channel_name, limit=command_top.limit)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            lines = ["ТОП БОГАЧЕЙ:"]
            for i, user in enumerate(top_users, 1):
                lines.append(f"{i}. {user.user_name}: {user.balance} монет.")
            result = "\n".join(lines)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_top.channel_name,
                user_name=command_top.user_name,
                content=user_message,
                current_time=command_top.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_top.channel_name,
                user_name=command_top.bot_nick,
                content=result,
                current_time=command_top.occurred_at,
            )

        return result

    async def handle_bottom(
        self,
        command_bottom: BottomDTO,
    ) -> str:
        user_message = command_bottom.command_prefix + command_bottom.command_name
        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_since = datetime.utcnow() - timedelta(days=30)
            bottom_users = uow.economy_policy.get_bottom_users(
                channel_name=command_bottom.channel_name, limit=command_bottom.limit, active_since=active_since
            )

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            lines = ["💸 ТОП БОМЖЕЙ:"]
            for i, user in enumerate(bottom_users, 1):
                lines.append(f"{i}. {user.user_name}: {user.balance} монет.")
            result = "\n".join(lines)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_bottom.channel_name,
                user_name=command_bottom.user_name,
                content=user_message,
                current_time=command_bottom.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_bottom.channel_name,
                user_name=command_bottom.bot_nick,
                content=result,
                current_time=command_bottom.occurred_at,
            )

        return result
