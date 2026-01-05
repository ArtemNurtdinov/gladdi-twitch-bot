from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.top_bottom.model import BottomDTO, TopDTO
from app.economy.domain.economy_policy import EconomyPolicy
from core.provider import Provider


class HandleTopBottomUseCase:
    def __init__(self, economy_policy_provider: Provider[EconomyPolicy], chat_use_case_provider: Provider[ChatUseCase]):
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_top(
        self,
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_top: TopDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            top_users = self._economy_policy_provider.get(db).get_top_users(command_top.channel_name, limit=command_top.limit)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            lines = ["ТОП БОГАЧЕЙ:"]
            for i, user in enumerate(top_users, 1):
                lines.append(f"{i}. {user.user_name}: {user.balance} монет.")
            result = "\n".join(lines)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_top.channel_name,
                user_name=command_top.bot_nick,
                content=result,
                current_time=command_top.occurred_at,
            )

        return result

    async def handle_bottom(
        self,
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_bottom: BottomDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            bottom_users = self._economy_policy_provider.get(db).get_bottom_users(command_bottom.channel_name, limit=command_bottom.limit)

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            lines = ["💸 ТОП БОМЖЕЙ:"]
            for i, user in enumerate(bottom_users, 1):
                lines.append(f"{i}. {user.user_name}: {user.balance} монет.")
            result = "\n".join(lines)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_bottom.channel_name,
                user_name=command_bottom.bot_nick,
                content=result,
                current_time=command_bottom.occurred_at,
            )

        return result
