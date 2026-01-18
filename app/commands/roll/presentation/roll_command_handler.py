from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.roll.application.handle_roll_use_case import HandleRollUseCase
from app.commands.roll.application.model import RollDTO
from app.moderation.application.chat_moderation_port import ChatModerationPort
from core.chat.interfaces import ChatContext


class RollCommandHandler:
    DEFAULT_COOLDOWN_SECONDS = 60
    CLEANUP_THRESHOLD_SECONDS = 300

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_roll_use_case: HandleRollUseCase,
        chat_moderation: ChatModerationPort,
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_roll_use_case = handle_roll_use_case
        self.roll_cooldowns: dict[str, datetime] = {}
        self._chat_moderation = chat_moderation
        self._bot_nick = bot_nick
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

    async def handle(self, chat_ctx: ChatContext, channel_name: str, display_name: str, amount: str | None = None):
        self._cleanup_old_cooldowns()

        dto = RollDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            amount_input=amount,
            last_roll_time=self.roll_cooldowns.get(display_name),
        )

        result = await self._handle_roll_use_case.handle(command_roll=dto)

        if result.new_last_roll_time:
            self.roll_cooldowns[display_name] = result.new_last_roll_time

        for message in result.messages:
            await self.post_message_fn(message, chat_ctx)

        if result.timeout_action:
            await self.post_message_fn(result.timeout_action.reason, chat_ctx)
            await self._chat_moderation.timeout_user(
                channel_name=channel_name,
                moderator_name=self._bot_nick,
                username=result.timeout_action.user_name,
                duration_seconds=result.timeout_action.duration_seconds,
                reason=result.timeout_action.reason,
            )
