import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.economy.domain.models import TransactionType
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_service import MinigameService


class MinigameOrchestrator:
    DEFAULT_SLEEP_SECONDS = 60

    def __init__(
        self,
        minigame_service: MinigameService,
        unit_of_work_factory: MinigameUnitOfWorkFactory,
        bot_nick: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        start_number_guess_game_use_case: StartNumberGuessGameUseCase,
        start_word_game_use_case: StartWordGameUseCase,
        start_rps_game_use_case: StartRpsGameUseCase,
    ):
        self.minigame_service = minigame_service
        self._unit_of_work_factory = unit_of_work_factory
        self._bot_nick = bot_nick
        self._send_channel_message = send_channel_message
        self._start_number_guess_game_use_case = start_number_guess_game_use_case
        self._start_word_game_use_case = start_word_game_use_case
        self._start_rps_game_use_case = start_rps_game_use_case

    def _bot_name_lower(self) -> str:
        return self._bot_nick.lower()

    async def run_tick(self, channel_name: str) -> int:
        rps_game_complete_time = self.minigame_service.check_rps_game_complete_time(channel_name, datetime.utcnow())
        if rps_game_complete_time:
            await self._finish_rps(channel_name)
            return self.DEFAULT_SLEEP_SECONDS

        await self._finish_expired_games()

        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(channel_name)

        if not active_stream:
            return self.DEFAULT_SLEEP_SECONDS

        if not self.minigame_service.should_start_new_game(channel_name):
            return self.DEFAULT_SLEEP_SECONDS

        choice = random.choice(["number", "word", "rps"])

        if choice == "word":
            await self._start_word_game_use_case.start(channel_name)
        elif choice == "number":
            await self._start_number_guess_game_use_case.start(channel_name)
        else:
            await self._start_rps_game_use_case.start(channel_name)

        return self.DEFAULT_SLEEP_SECONDS

    async def _finish_rps(self, channel_name: str):
        game = self.minigame_service.get_active_rps_game(channel_name)
        bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game, channel_name)

        if winners:
            share = max(1, game.bank // len(winners))
            with self._unit_of_work_factory.create() as uow:
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

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name_lower(), content=message, current_time=datetime.utcnow()
            )

        await self._send_channel_message(channel_name, message)
        await asyncio.sleep(60)

    async def _finish_expired_games(self):
        expired_games = self.minigame_service.check_expired_games()
        for channel, timeout_message in expired_games.items():
            await self._send_channel_message(channel, timeout_message)
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=channel, user_name=self._bot_name_lower(), content=timeout_message, current_time=datetime.utcnow()
                )
