import random
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.economy.domain.models import TransactionType
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.infrastructure.minigame_repository import RPS_CHOICES
from app.shop.domain.model.effect import MinigamePrizeMultiplierEffect


class FinishRpsUseCase:
    def __init__(
        self,
        minigame_repository: MinigameRepository,
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
        send_channel_message: Callable[[str], Awaitable[None]],
    ):
        self._minigame_repository = minigame_repository
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name
        self._send_channel_message = send_channel_message

    async def finish(self, channel_name: str):
        game = self._minigame_repository.get_active_rps_game(channel_name)

        if not game:
            return

        bot_choice = random.choice(RPS_CHOICES)
        counter_map = {
            "камень": "бумага",
            "бумага": "ножницы",
            "ножницы": "камень",
        }
        winning_choice = counter_map[bot_choice]
        game.winner_choice = winning_choice
        winners = [user for user, choice in game.user_choices.items() if choice == game.winner_choice]

        if winners:
            share = max(1, game.bank // len(winners))
            messages = []
            with self._minigame_uow.create() as uow:
                for winner in winners:
                    messages.append(f"Победитель @{winner}.")

                    multiplier = 1.0

                    user_equipment = uow.get_user_equipment_use_case.get_user_equipment(channel_name, winner)

                    for equipment in user_equipment:
                        for effect in equipment.shop_item.effects:
                            if isinstance(effect, MinigamePrizeMultiplierEffect):
                                multiplier *= effect.multiplier
                                messages.append(effect.message)

                    prize = int(share * multiplier)

                    messages.append(f"Сумма выигрыша {prize}.")

                    uow.economy_policy.add_balance(
                        channel_name=channel_name,
                        user_name=winner,
                        amount=prize,
                        transaction_type=TransactionType.MINIGAME_WIN,
                        description=f"Победа в КНБ ({winning_choice})",
                    )

            message = f"Выбор бота: {bot_choice}. Банк: {game.bank}. Побеждает вариант: {winning_choice}. {' '.join(messages)}"
        else:
            message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."

        self._minigame_repository.delete_active_rps_game(channel_name)

        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=message, current_time=datetime.utcnow()
            )

        await self._send_channel_message(message)
