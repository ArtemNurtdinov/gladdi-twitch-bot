from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_service import MinigameService
from core.db import SessionLocal


class GuessCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_guess: str,
        command_guess_letter: str,
        command_guess_word: str,
        minigame_service: MinigameService,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]]
    ):
        self.command_prefix = command_prefix
        self.command_guess = command_guess
        self.command_guess_letter = command_guess_letter
        self.command_guess_word = command_guess_word
        self.minigame_service = minigame_service
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.nick_provider = nick_provider
        self.post_message_fn = post_message_fn

    async def handle_guess_number(self, channel_name: str, display_name: str, ctx, number: str | None):
        bot_nick = (self.nick_provider() or "").lower()
        user_name = display_name.lower()

        if not number:
            result = f"@{display_name}, используй: {self.command_prefix}{self.command_guess} [число]"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        try:
            guess = int(number)
        except ValueError:
            result = f"@{display_name}, укажи правильное число! Например: {self.command_prefix}{self.command_guess} 42"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if not self.minigame_service.is_game_active(channel_name):
            result = "Сейчас нет активной игры 'угадай число'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        game = self.minigame_service.get_active_game(channel_name)

        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_guess_game_timeout(channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if not game.is_active:
            result = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if not game.min_number <= guess <= game.max_number:
            result = f"Число должно быть от {game.min_number} до {game.max_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if guess == game.target_number:
            self.minigame_service.finish_game_with_winner(game, channel_name, display_name, guess)
            description = f"Победа в игре 'угадай число': {guess}"
            message = f"ПОЗДРАВЛЯЕМ! @{display_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with SessionLocal.begin() as db:
                self._economy_service(db).add_balance(
                    channel_name, user_name, game.prize_amount, TransactionType.MINIGAME_WIN, description
                )
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - MinigameService.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{display_name}, не угадал! Загаданное число {hint} {guess}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)

    async def handle_guess_letter(self, channel_name: str, display_name: str, ctx, letter: str | None):
        bot_nick = (self.nick_provider() or "").lower()
        user_name = display_name.lower()

        if not letter:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await self.post_message_fn(status, ctx)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, status, datetime.utcnow())
            else:
                message = f"@{display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
                await self.post_message_fn(message, ctx)
            return

        word_game_is_active = self.minigame_service.is_word_game_active(channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

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
                with SessionLocal.begin() as db:
                    winner_balance = self._economy_service(db).add_balance(
                        channel_name,
                        user_name,
                        game.prize_amount,
                        TransactionType.MINIGAME_WIN,
                        "Победа в игре 'поле чудес'",
                    )

                message = (
                    f"ПОЗДРАВЛЯЕМ! @{display_name} угадал слово '{game.target_word}' и выиграл "
                    f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
                )
                self.minigame_service.finish_word_game_with_winner(game, channel_name, display_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)

    async def handle_guess_word(self, channel_name: str, display_name: str, ctx, word: str | None):
        bot_nick = (self.nick_provider() or "").lower()
        user_name = display_name.lower()

        if not word:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await self.post_message_fn(status, ctx)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, status, datetime.utcnow())
            else:
                message = f"@{display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
                await self.post_message_fn(message, ctx)
            return

        word_game_is_active = self.minigame_service.is_word_game_active(channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if word.strip().lower() == game.target_word:
            self.minigame_service.finish_word_game_with_winner(game, channel_name, display_name)

            with SessionLocal.begin() as db:
                winner_balance = self._economy_service(db).add_balance(
                    channel_name,
                    user_name,
                    game.prize_amount,
                    TransactionType.MINIGAME_WIN,
                    "Победа в игре 'поле чудес'",
                )

            message = (
                f"ПОЗДРАВЛЯЕМ! @{display_name} угадал слово '{game.target_word}' и выиграл "
                f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
