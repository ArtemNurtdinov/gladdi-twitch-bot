from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.commands.roll.handle_roll_use_case import HandleRollUseCase
from app.commands.roll.model import RollDTO


class RollCommandHandler:
    DEFAULT_COOLDOWN_SECONDS = 60
    CLEANUP_THRESHOLD_SECONDS = 300

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_roll_use_case: HandleRollUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        timeout_fn: Callable[[str, str, int, str], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_roll_use_case = handle_roll_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.roll_cooldowns: dict[str, datetime] = {}
        self.timeout_user = timeout_fn
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    def _cleanup_old_cooldowns(self):
        current_time = datetime.now()
        cleanup_threshold = self.CLEANUP_THRESHOLD_SECONDS

        nicknames = [
            nickname
            for nickname, last_time in self.roll_cooldowns.items()
            if (current_time - last_time).total_seconds() > cleanup_threshold
        ]

        for nickname in nicknames:
            del self.roll_cooldowns[nickname]

    async def handle(self, ctx, channel_name: str, display_name: str, amount: str | None = None):
        self._cleanup_old_cooldowns()

        dto = RollDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
            amount_input=amount,
            last_roll_time=self.roll_cooldowns.get(display_name),
        )

        result = await self._handle_roll_use_case.handle(
            db_session_provider=self._db_session_provider, db_readonly_session_provider=self._db_readonly_session_provider, command_roll=dto
        )

        if result.new_last_roll_time:
            self.roll_cooldowns[display_name] = result.new_last_roll_time

        for message in result.messages:
            await self.post_message_fn(message, ctx)

        if result.timeout_action:
            await self.post_message_fn(result.timeout_action.reason, ctx)
            await self.timeout_user(
                channel_name,
                result.timeout_action.user_name,
                result.timeout_action.duration_seconds,
                result.timeout_action.reason,
            )
