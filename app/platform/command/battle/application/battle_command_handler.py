from datetime import UTC, datetime

from app.moderation.application.timeout_use_case import TimeoutUseCase
from app.platform.command.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.platform.command.battle.application.model import BattleDTO
from app.platform.command.domain.command_handler import CommandHandler


class BattleCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_battle_use_case: HandleBattleUseCase,
        timeout_use_case: TimeoutUseCase,
        battle_waiting_user: dict[str, str | None],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._handle_battle_use_case = handle_battle_use_case
        self._timeout_use_case = timeout_use_case
        self._bot_name: str | None = None
        self._battle_waiting_user = battle_waiting_user

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        battle = BattleDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            message=message,
            command_call=f"{self.command_prefix}{self.command_name}",
            waiting_user=self._battle_waiting_user["value"],
        )

        result = await self._handle_battle_use_case.handle(command_battle=battle)

        self._battle_waiting_user["value"] = result.new_waiting_user

        response_message = "\n".join(result.messages) if result.messages else None

        if result.timeout_action:
            await self._timeout_use_case.timeout_user(
                channel_name=channel_name,
                moderator_name=self._bot_name,
                username=result.timeout_action.user_name,
                duration_seconds=result.timeout_action.duration_seconds,
                reason=result.timeout_action.reason,
            )

        return response_message
