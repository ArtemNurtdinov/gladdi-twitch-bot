from collections.abc import Awaitable, Callable
from datetime import datetime

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_repository import MinigameRepository


class FinishExpiredGamesUseCase:
    def __init__(
        self,
        minigame_repository: MinigameRepository,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
    ):
        self._minigame_repository = minigame_repository
        self._send_channel_message = send_channel_message
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name

    async def finish(self, channel_name: str) -> None:
        expired_games: dict[str, str] = {}

        active_guess_game = self._minigame_repository.get_active_guess_game(channel_name)

        if active_guess_game and datetime.utcnow() > active_guess_game.end_time and active_guess_game.is_active:
            active_guess_game.is_active = False
            self._minigame_repository.delete_guess_game(channel_name)
            timeout_message = (
                f"Время игры 'угадай число' истекло! Загаданное число было {active_guess_game.target_number}. Никто не выиграл."
            )
            expired_games[channel_name] = timeout_message

        active_word_game = self._minigame_repository.get_active_word_game(channel_name)

        if active_word_game and datetime.utcnow() > active_word_game.end_time and active_word_game.is_active:
            active_word_game.is_active = False
            expired_games[channel_name] = f"Время игры 'поле чудес' истекло! Слово было '{active_word_game.target_word}'. Никто не выиграл."

        for channel, timeout_message in expired_games.items():
            await self._send_channel_message(channel, timeout_message)
            with self._minigame_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=channel, user_name=self._bot_name, content=timeout_message, current_time=datetime.utcnow()
                )
