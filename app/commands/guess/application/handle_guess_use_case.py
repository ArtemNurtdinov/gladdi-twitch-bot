from datetime import datetime

from app.commands.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.commands.guess.application.model import GuessLetterDTO, GuessNumberDTO, GuessWordDTO
from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_repository import MinigameRepository


class HandleGuessUseCase:
    WORD_GAME_MIN_PRIZE = 300
    WORD_GAME_LETTER_REWARD_DECREASE = 200
    GUESS_PRIZE_DECREASE_PER_ATTEMPT = 100

    def __init__(self, minigame_repository: MinigameRepository, guess_uow: GuessUnitOfWorkFactory):
        self._minigame_repository = minigame_repository
        self._guess_uow = guess_uow

    async def handle_number(self, guess_number: GuessNumberDTO) -> str:
        command_prefix = guess_number.command_prefix
        command_guess = guess_number.command_guess
        user_message = guess_number.command_prefix + guess_number.command_guess
        if guess_number.guess_input:
            user_message += f" {guess_number.guess_input}"
        if not guess_number.guess_input:
            result = f"@{guess_number.display_name}, используй: {command_prefix}{command_guess} [число]"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result
        try:
            guess = int(guess_number.guess_input)
        except ValueError:
            result = f"@{guess_number.display_name}, укажи число! Например: {command_prefix}{command_guess} 42"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result

        game = self._minigame_repository.get_active_guess_game(guess_number.channel_name)

        if not game:
            result = "Сейчас нет активной игры 'угадай число'"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result

        if datetime.utcnow() > game.end_time:
            game.is_active = False
            self._minigame_repository.delete_guess_game(guess_number.channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result

        if not game.is_active:
            result = "Игра уже завершена"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result

        if not game.min_number <= guess <= game.max_number:
            result = f"Число должно быть от {game.min_number} до {game.max_number}"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=result,
                    current_time=guess_number.occurred_at,
                )
            return result

        if guess == game.target_number:
            game.is_active = False
            game.winner = guess_number.display_name
            game.winning_time = datetime.utcnow()
            self._minigame_repository.delete_guess_number_game(guess_number.channel_name)

            message = f"ПОЗДРАВЛЯЕМ! @{guess_number.display_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with self._guess_uow.create() as uow:
                uow.economy_policy.add_balance(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    amount=game.prize_amount,
                    transaction_type=TransactionType.MINIGAME_WIN,
                    description=f"Победа в игре 'угадай число': {guess}",
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=message,
                    current_time=guess_number.occurred_at,
                )
            return message
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - self.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{guess_number.display_name}, не угадал! Загаданное число {hint} {guess}."
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.user_name,
                    content=user_message,
                    current_time=guess_number.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_number.channel_name,
                    user_name=guess_number.bot_nick,
                    content=message,
                    current_time=guess_number.occurred_at,
                )
            return message

    async def handle_letter(self, guess_letter: GuessLetterDTO) -> str:
        user_message = guess_letter.command_prefix + guess_letter.command_name

        if guess_letter.letter_input:
            user_message += guess_letter.letter_input

        game = self._minigame_repository.get_active_word_game(guess_letter.channel_name)

        if not game:
            message = "Сейчас нет активной игры 'поле чудес'"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )
            return message

        if not guess_letter.letter_input:
            if datetime.utcnow() > game.end_time:
                game.is_active = False
                message = f"Время игры 'поле чудес' истекло! Слово было '{game.target_word}'. Никто не выиграл."
                self._minigame_repository.delete_word_guess_game(guess_letter.channel_name)
            else:
                if game.winner:
                    message = f"Слово '{game.target_word}' угадал @{game.winner}! Выигрыш: {game.prize_amount} монет"
                elif not game.is_active:
                    message = f"Время истекло! Слово было '{game.target_word}'"
                else:
                    letters_count = sum(1 for ch in game.target_word if ch.isalpha())
                    message = f"Угадайте слово из {letters_count} букв! Слово: {game.get_masked_word()}"

            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )

            return message

        if datetime.utcnow() > game.end_time:
            game.is_active = False
            self._minigame_repository.delete_word_guess_game(guess_letter.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )
            return message

        letter = guess_letter.letter_input

        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )
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
            if game.prize_amount > self.WORD_GAME_MIN_PRIZE:
                current_prize = game.prize_amount - self.WORD_GAME_LETTER_REWARD_DECREASE
                game.prize_amount = max(self.WORD_GAME_MIN_PRIZE, current_prize)
            letters_in_word = {ch for ch in game.target_word if ch.isalpha()}
            all_letters_revealed = letters_in_word.issubset(game.guessed_letters)
            if all_letters_revealed:
                message = (
                    f"ПОЗДРАВЛЯЕМ! @{guess_letter.display_name} угадал слово '{game.target_word}' и выиграл {game.prize_amount} монет!"
                )
                with self._guess_uow.create() as uow:
                    uow.economy_policy.add_balance(
                        channel_name=guess_letter.channel_name,
                        user_name=guess_letter.user_name,
                        amount=game.prize_amount,
                        transaction_type=TransactionType.MINIGAME_WIN,
                        description="Победа в игре 'поле чудес'",
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_letter.channel_name,
                        user_name=guess_letter.user_name,
                        content=user_message,
                        current_time=guess_letter.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_letter.channel_name,
                        user_name=guess_letter.bot_nick,
                        content=message,
                        current_time=guess_letter.occurred_at,
                    )
                game.is_active = False
                game.winner = guess_letter.display_name
                game.winning_time = datetime.utcnow()

                self._minigame_repository.delete_word_guess_game(guess_letter.channel_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.user_name,
                    content=user_message,
                    current_time=guess_letter.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter.channel_name,
                    user_name=guess_letter.bot_nick,
                    content=message,
                    current_time=guess_letter.occurred_at,
                )

        return message

    async def handle_word(self, guess_word: GuessWordDTO) -> str:
        user_message = guess_word.command_prefix + guess_word.command_name
        if guess_word.word_input:
            user_message += guess_word.word_input

        game = self._minigame_repository.get_active_word_game(guess_word.channel_name)

        if not game:
            message = "Сейчас нет активной игры 'поле чудес'"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    content=user_message,
                    current_time=guess_word.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.bot_nick,
                    content=message,
                    current_time=guess_word.occurred_at,
                )
            return message

        if not guess_word.word_input:
            if datetime.utcnow() > game.end_time:
                message = f"Время игры 'поле чудес' истекло! Слово было '{game.target_word}'. Никто не выиграл."
                game.is_active = False
                self._minigame_repository.delete_word_guess_game(guess_word.channel_name)
            else:
                if game.winner:
                    message = f"Слово '{game.target_word}' угадал @{game.winner}! Выигрыш: {game.prize_amount} монет"
                elif not game.is_active:
                    message = f"Время истекло! Слово было '{game.target_word}'"
                else:
                    letters_count = sum(1 for ch in game.target_word if ch.isalpha())
                    message = f"Угадайте слово из {letters_count} букв! Слово: {game.get_masked_word()}"

            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    content=user_message,
                    current_time=guess_word.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.bot_nick,
                    content=message,
                    current_time=guess_word.occurred_at,
                )
            return message

        if datetime.utcnow() > game.end_time:
            game.is_active = False
            self._minigame_repository.delete_word_guess_game(guess_word.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    content=user_message,
                    current_time=guess_word.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.bot_nick,
                    content=message,
                    current_time=guess_word.occurred_at,
                )
            return message

        if guess_word.word_input.strip().lower() == game.target_word:
            game.is_active = False
            game.winner = guess_word.display_name
            game.winning_time = datetime.utcnow()

            self._minigame_repository.delete_word_guess_game(guess_word.channel_name)

            message = f"ПОЗДРАВЛЯЕМ! @{guess_word.display_name} угадал слово '{game.target_word}' и выиграл {game.prize_amount} монет!"

            with self._guess_uow.create() as uow:
                uow.economy_policy.add_balance(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    amount=game.prize_amount,
                    transaction_type=TransactionType.MINIGAME_WIN,
                    description="Победа в игре 'поле чудес'",
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    content=user_message,
                    current_time=guess_word.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.bot_nick,
                    content=message,
                    current_time=guess_word.occurred_at,
                )

        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with self._guess_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.user_name,
                    content=user_message,
                    current_time=guess_word.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word.channel_name,
                    user_name=guess_word.bot_nick,
                    content=message,
                    current_time=guess_word.occurred_at,
                )

        return message
