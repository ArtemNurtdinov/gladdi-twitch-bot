from datetime import datetime
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_service import MinigameService
from app.twitch.application.interaction.guess.dto import GuessLetterDTO, GuessNumberDTO, GuessWordDTO
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.economy_service_provider import EconomyServiceProvider


class HandleGuessUseCase:

    def __init__(
        self,
        minigame_service: MinigameService,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
    ):
        self._minigame_service = minigame_service
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_number(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: GuessNumberDTO,
    ) -> str:
        if not dto.guess_input:
            result = f"@{dto.display_name}, используй: {dto.command_prefix}{dto.command_guess} [число]"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result
        try:
            guess = int(dto.guess_input)
        except ValueError:
            result = f"@{dto.display_name}, укажи число! Например: {dto.command_prefix}{dto.command_guess} 42"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        if not self._minigame_service.is_game_active(dto.channel_name):
            result = "Сейчас нет активной игры 'угадай число'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        game = self._minigame_service.get_active_game(dto.channel_name)

        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_guess_game_timeout(dto.channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        if not game.is_active:
            result = "Игра уже завершена"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        if not game.min_number <= guess <= game.max_number:
            result = f"Число должно быть от {game.min_number} до {game.max_number}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        if guess == game.target_number:
            self._minigame_service.finish_game_with_winner(game, dto.channel_name, dto.display_name, guess)
            description = f"Победа в игре 'угадай число': {guess}"
            message = f"ПОЗДРАВЛЯЕМ! @{dto.display_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with db_session_provider() as db:
                self._economy_service_provider.get(db).add_balance(
                    dto.channel_name,
                    dto.user_name,
                    game.prize_amount,
                    TransactionType.MINIGAME_WIN,
                    description,
                )
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - MinigameService.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{dto.display_name}, не угадал! Загаданное число {hint} {guess}."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

    async def handle_letter(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: GuessLetterDTO,
    ) -> str:
        if not dto.letter_input:
            status = self._minigame_service.get_word_game_status(dto.channel_name)
            if status:
                message = status
                with db_session_provider() as db:
                    self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, status, dto.occurred_at)
            else:
                message = f"@{dto.display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
            return message
        word_game_is_active = self._minigame_service.is_word_game_active(dto.channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        game = self._minigame_service.get_active_word_game(dto.channel_name)
        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_word_game_timeout(dto.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        letter = dto.letter_input
        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        letter_revealed = False
        letter = letter.lower()
        if letter in game.guessed_letters:
            letter_revealed = False
        if letter in game.target_word:
            game.guessed_letters.add(letter)
            letter_revealed = True

        masked = game.get_masked_word()

        if letter_revealed:
            if game.prize_amount > MinigameService.WORD_GAME_MIN_PRIZE:
                game.prize_amount = max(
                    MinigameService.WORD_GAME_MIN_PRIZE,
                    game.prize_amount - MinigameService.WORD_GAME_LETTER_REWARD_DECREASE,
                )
            letters_in_word = {ch for ch in game.target_word if ch.isalpha()}
            all_letters_revealed = letters_in_word.issubset(game.guessed_letters)
            if all_letters_revealed:
                with db_session_provider() as db:
                    winner_balance = self._economy_service_provider.get(db).add_balance(
                        dto.channel_name,
                        dto.user_name,
                        game.prize_amount,
                        TransactionType.MINIGAME_WIN,
                        "Победа в игре 'поле чудес'",
                    )
                message = (
                    f"ПОЗДРАВЛЯЕМ! @{dto.display_name} угадал слово '{game.target_word}' и выиграл "
                    f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
                )
                self._minigame_service.finish_word_game_with_winner(game, dto.channel_name, dto.display_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)

        return message

    async def handle_word(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: GuessWordDTO,
    ) -> str:
        if not dto.word_input:
            status = self._minigame_service.get_word_game_status(dto.channel_name)
            if status:
                message = status
                with db_session_provider() as db:
                    self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, status, dto.occurred_at)
            else:
                message = f"@{dto.display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
            return message

        word_game_is_active = self._minigame_service.is_word_game_active(dto.channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        game = self._minigame_service.get_active_word_game(dto.channel_name)
        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_word_game_timeout(dto.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
            return message

        if dto.word_input.strip().lower() == game.target_word:
            self._minigame_service.finish_word_game_with_winner(game, dto.channel_name, dto.display_name)

            with db_session_provider() as db:
                winner_balance = self._economy_service_provider.get(db).add_balance(
                    dto.channel_name,
                    dto.user_name,
                    game.prize_amount,
                    TransactionType.MINIGAME_WIN,
                    "Победа в игре 'поле чудес'",
                )

            message = (
                f"ПОЗДРАВЛЯЕМ! @{dto.display_name} угадал слово '{game.target_word}' и выиграл "
                f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)
        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, message, dto.occurred_at)

        return message
