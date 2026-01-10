import asyncio
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.battle.handle_battle_use_case import HandleBattleUseCase
from app.commands.battle.model import BattleDTO
from app.moderation.application.chat_moderation_port import ChatModerationPort
from core.chat.interfaces import ChatContext


class BattleCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_battle_use_case: HandleBattleUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        chat_moderation: ChatModerationPort,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_battle_use_case = handle_battle_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self._chat_moderation = chat_moderation
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, battle_waiting_user_ref, chat_ctx: ChatContext):
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
            await self.post_message_fn(message, chat_ctx)

        if result.delay_before_timeout:
            await asyncio.sleep(result.delay_before_timeout)

        if result.timeout_action:
            await self._chat_moderation.timeout_user(
                channel_name=channel_name,
                moderator_name=self.bot_nick_provider(),
                username=result.timeout_action.user_name,
                duration_seconds=result.timeout_action.duration_seconds,
                reason=result.timeout_action.reason,
            )
