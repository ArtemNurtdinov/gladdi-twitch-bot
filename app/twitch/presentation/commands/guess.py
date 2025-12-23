import logging
from datetime import datetime
from typing import Callable

from core.db import SessionLocal, db_ro_session
from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_service import MinigameService

logger = logging.getLogger(__name__)


class GuessCommandHandler:
    """Обработчики игр угадай число / букву / слово."""

    def __init__(
        self,
        minigame_service: MinigameService,
        economy_service_factory,
        chat_use_case_factory,
        command_guess: str,
        command_guess_letter: str,
        command_guess_word: str,
        prefix: str,
        nick_provider: Callable[[], str],
    ):
        self.minigame_service = minigame_service
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_guess = command_guess
        self.command_guess_letter = command_guess_letter
        self.command_guess_word = command_guess_word
        self.prefix = prefix
        self.nick_provider = nick_provider

    async def handle_guess_number(self, ctx, number: str | None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = (self.nick_provider() or "").lower()

        logger.info(f"Команда {self.command_guess} от пользователя {user_name}, число: {number}")
        if not number:
            result = f"@{user_name}, используй: {self.prefix}{self.command_guess} [число]"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            guess = int(number)
        except ValueError:
            result = f"@{user_name}, укажи правильное число! Например: {self.prefix}{self.command_guess} 42"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        if not self.minigame_service.is_game_active(channel_name):
            result = "Сейчас нет активной игры 'угадай число'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        game = self.minigame_service.get_active_game(channel_name)

        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_guess_game_timeout(channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        if not game.is_active:
            result = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        if not game.min_number <= guess <= game.max_number:
            result = f"Число должно быть от {game.min_number} до {game.max_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await ctx.send(result)
            return

        if guess == game.target_number:
            self.minigame_service.finish_game_with_winner(game, channel_name, user_name, guess)
            description = f"Победа в игре 'угадай число': {guess}"
            message = f"ПОЗДРАВЛЯЕМ! @{user_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with SessionLocal.begin() as db:
                self._economy_service(db).add_balance(
                    channel_name, user_name.lower(), game.prize_amount, TransactionType.MINIGAME_WIN, description
                )
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - MinigameService.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{user_name}, не угадал! Загаданное число {hint} {guess}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)

    async def handle_guess_letter(self, ctx, letter: str | None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = (self.nick_provider() or "").lower()

        if not letter:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, status, datetime.utcnow())
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return

        word_game_is_active = self.minigame_service.is_word_game_active(channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
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
                normalized_user_name = user_name.lower()

                with SessionLocal.begin() as db:
                    winner_balance = self._economy_service(db).add_balance(
                        channel_name,
                        normalized_user_name,
                        game.prize_amount,
                        TransactionType.MINIGAME_WIN,
                        "Победа в игре 'поле чудес'",
                    )

                message = (
                    f"ПОЗДРАВЛЯЕМ! @{user_name} угадал слово '{game.target_word}' и выиграл "
                    f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
                )
                self.minigame_service.finish_word_game_with_winner(game, channel_name, user_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)

    async def handle_guess_word(self, ctx, word: str | None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = (self.nick_provider() or "").lower()

        if not word:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, status, datetime.utcnow())
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return

        word_game_is_active = self.minigame_service.is_word_game_active(channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
            return

        if word.strip().lower() == game.target_word:
            self.minigame_service.finish_word_game_with_winner(game, channel_name, user_name)
            normalized_user_name = user_name.lower()

            with SessionLocal.begin() as db:
                winner_balance = self._economy_service(db).add_balance(
                    channel_name,
                    normalized_user_name,
                    game.prize_amount,
                    TransactionType.MINIGAME_WIN,
                    "Победа в игре 'поле чудес'",
                )

            message = (
                f"ПОЗДРАВЛЯЕМ! @{user_name} угадал слово '{game.target_word}' и выиграл "
                f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)
        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await ctx.send(message)

