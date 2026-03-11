from collections.abc import Awaitable, Callable
from datetime import datetime

from app.economy.domain.models import TransactionType
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_service import MinigameService


class FinishRpsUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
    ):
        self._minigame_service = minigame_service
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name
        self._send_channel_message = send_channel_message

    async def finish(self, channel_name: str):
        game = self._minigame_service.get_active_rps_game(channel_name)

        if not game:
            return

        bot_choice, winning_choice, winners = self._minigame_service.finish_rps(game, channel_name)
        if winners:
            share = max(1, game.bank // len(winners))
            with self._minigame_uow.create() as uow:
                for winner in winners:
                    uow.economy_policy.add_balance(
                        channel_name=channel_name,
                        user_name=winner,
                        amount=share,
                        transaction_type=TransactionType.MINIGAME_WIN,
                        description=f"Победа в КНБ ({winning_choice})",
                    )
            winners_display = ", ".join(f"@{winner}" for winner in winners)
            message = (
                f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. "
                f"Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
            )
        else:
            message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."

        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=message, current_time=datetime.utcnow()
            )

        await self._send_channel_message(channel_name, message)
