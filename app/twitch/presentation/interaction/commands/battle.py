import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.commands.battle.model import BattleDTO
from app.commands.battle.handle_battle_use_case import HandleBattleUseCase


class BattleCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_battle_use_case: HandleBattleUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        timeout_fn: Callable[[str, str, int, str], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_battle_use_case = handle_battle_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.timeout_user = timeout_fn
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, battle_waiting_user_ref, ctx):
        battle_dto = BattleDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
            command_call=f"{self.command_prefix}{self.command_name}",
            waiting_user=battle_waiting_user_ref["value"],
        )

        result = await self._handle_battle_use_case.handle(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            command_battle=battle_dto,
        )

        battle_waiting_user_ref["value"] = result.new_waiting_user

        for message in result.messages:
            await self.post_message_fn(message, ctx)

        if result.delay_before_timeout:
            await asyncio.sleep(result.delay_before_timeout)

        if result.timeout_action:
            await self.timeout_user(
                channel_name,
                result.timeout_action.user_name,
                result.timeout_action.duration_seconds,
                result.timeout_action.reason,
            )
