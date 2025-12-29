from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.twitch.application.interaction.top_bottom.dto import BottomDTO, TopDTO
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.economy.application.economy_service_provider import EconomyServiceProvider


class HandleTopBottomUseCase:

    def __init__(
        self,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider
    ):
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_top(
        self,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        db_session_provider: Callable[[], ContextManager[Session]],
        command_top: TopDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            top_users = self._economy_service_provider.get(db).get_top_users(command_top.channel_name, limit=command_top.limit)

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
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        db_session_provider: Callable[[], ContextManager[Session]],
        command_bottom: BottomDTO,
    ) -> str:
        with db_readonly_session_provider() as db:
            bottom_users = self._economy_service_provider.get(db).get_bottom_users(command_bottom.channel_name, limit=command_bottom.limit)

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

