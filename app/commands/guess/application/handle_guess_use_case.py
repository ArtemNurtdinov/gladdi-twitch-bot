from datetime import datetime

from app.commands.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.commands.guess.application.model import GuessLetterDTO, GuessNumberDTO, GuessWordDTO
from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_service import MinigameService


class HandleGuessUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        unit_of_work_factory: GuessUnitOfWorkFactory,
    ):
        self._minigame_service = minigame_service
        self._unit_of_work_factory = unit_of_work_factory

    async def handle_number(
        self,
        guess_number: GuessNumberDTO,
    ) -> str:
        command_prefix = guess_number.command_prefix
        command_guess = guess_number.command_guess
        user_message = guess_number.command_prefix + guess_number.command_guess
        if guess_number.guess_input:
            user_message += f" {guess_number.guess_input}"
        if not guess_number.guess_input:
            result = f"@{guess_number.display_name}, используй: {command_prefix}{command_guess} [число]"
            with self._unit_of_work_factory.create() as uow:
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
            with self._unit_of_work_factory.create() as uow:
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

        if not self._minigame_service.is_game_active(guess_number.channel_name):
            result = "Сейчас нет активной игры 'угадай число'"
            with self._unit_of_work_factory.create() as uow:
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

        game = self._minigame_service.get_active_game(guess_number.channel_name)

        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_guess_game_timeout(guess_number.channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with self._unit_of_work_factory.create() as uow:
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
            with self._unit_of_work_factory.create() as uow:
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
            with self._unit_of_work_factory.create() as uow:
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
            self._minigame_service.finish_game_with_winner(game, guess_number.channel_name, guess_number.display_name)
            message = f"ПОЗДРАВЛЯЕМ! @{guess_number.display_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with self._unit_of_work_factory.create() as uow:
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
                game.prize_amount = max(300, game.prize_amount - MinigameService.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{guess_number.display_name}, не угадал! Загаданное число {hint} {guess}."
            with self._unit_of_work_factory.create() as uow:
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

    async def handle_letter(
        self,
        guess_letter_dto: GuessLetterDTO,
    ) -> str:
        user_message = guess_letter_dto.command_prefix + guess_letter_dto.command_name

        if guess_letter_dto.letter_input:
            user_message += guess_letter_dto.letter_input

        if not guess_letter_dto.letter_input:
            status = self._minigame_service.get_word_game_status(guess_letter_dto.channel_name)
            if status:
                message = status
                with self._unit_of_work_factory.create() as uow:
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_letter_dto.channel_name,
                        user_name=guess_letter_dto.user_name,
                        content=user_message,
                        current_time=guess_letter_dto.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_letter_dto.channel_name,
                        user_name=guess_letter_dto.bot_nick,
                        content=status,
                        current_time=guess_letter_dto.occurred_at,
                    )
            else:
                message = f"@{guess_letter_dto.display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
            return message
        word_game_is_active = self._minigame_service.is_word_game_active(guess_letter_dto.channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
                )
            return message

        game = self._minigame_service.get_active_word_game(guess_letter_dto.channel_name)
        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_word_game_timeout(guess_letter_dto.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
                )
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
                )
            return message

        letter = guess_letter_dto.letter_input
        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
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
            if game.prize_amount > MinigameService.WORD_GAME_MIN_PRIZE:
                current_prize = game.prize_amount - MinigameService.WORD_GAME_LETTER_REWARD_DECREASE
                game.prize_amount = max(MinigameService.WORD_GAME_MIN_PRIZE, current_prize)
            letters_in_word = {ch for ch in game.target_word if ch.isalpha()}
            all_letters_revealed = letters_in_word.issubset(game.guessed_letters)
            if all_letters_revealed:
                with self._unit_of_work_factory.create() as uow:
                    winner_balance = uow.economy_policy.add_balance(
                        channel_name=guess_letter_dto.channel_name,
                        user_name=guess_letter_dto.user_name,
                        amount=game.prize_amount,
                        transaction_type=TransactionType.MINIGAME_WIN,
                        description="Победа в игре 'поле чудес'",
                    )
                message = (
                    f"ПОЗДРАВЛЯЕМ! @{guess_letter_dto.display_name} угадал слово '{game.target_word}' и выиграл "
                    f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
                )
                self._minigame_service.finish_word_game_with_winner(game, guess_letter_dto.channel_name, guess_letter_dto.display_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
                )
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.user_name,
                    content=user_message,
                    current_time=guess_letter_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_letter_dto.channel_name,
                    user_name=guess_letter_dto.bot_nick,
                    content=message,
                    current_time=guess_letter_dto.occurred_at,
                )

        return message

    async def handle_word(
        self,
        guess_word_dto: GuessWordDTO,
    ) -> str:
        user_message = guess_word_dto.command_prefix + guess_word_dto.command_name
        if guess_word_dto.word_input:
            user_message += guess_word_dto.word_input

        if not guess_word_dto.word_input:
            status = self._minigame_service.get_word_game_status(guess_word_dto.channel_name)
            if status:
                message = status
                with self._unit_of_work_factory.create() as uow:
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_word_dto.channel_name,
                        user_name=guess_word_dto.user_name,
                        content=user_message,
                        current_time=guess_word_dto.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=guess_word_dto.channel_name,
                        user_name=guess_word_dto.bot_nick,
                        content=status,
                        current_time=guess_word_dto.occurred_at,
                    )
            else:
                message = f"@{guess_word_dto.display_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска."
            return message

        word_game_is_active = self._minigame_service.is_word_game_active(guess_word_dto.channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    content=user_message,
                    current_time=guess_word_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.bot_nick,
                    content=message,
                    current_time=guess_word_dto.occurred_at,
                )
            return message

        game = self._minigame_service.get_active_word_game(guess_word_dto.channel_name)
        if datetime.utcnow() > game.end_time:
            self._minigame_service.finish_word_game_timeout(guess_word_dto.channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    content=user_message,
                    current_time=guess_word_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.bot_nick,
                    content=message,
                    current_time=guess_word_dto.occurred_at,
                )
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    content=user_message,
                    current_time=guess_word_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.bot_nick,
                    content=message,
                    current_time=guess_word_dto.occurred_at,
                )
            return message

        if guess_word_dto.word_input.strip().lower() == game.target_word:
            self._minigame_service.finish_word_game_with_winner(game, guess_word_dto.channel_name, guess_word_dto.display_name)

            with self._unit_of_work_factory.create() as uow:
                winner_balance = uow.economy_policy.add_balance(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    amount=game.prize_amount,
                    transaction_type=TransactionType.MINIGAME_WIN,
                    description="Победа в игре 'поле чудес'",
                )

            message = (
                f"ПОЗДРАВЛЯЕМ! @{guess_word_dto.display_name} угадал слово '{game.target_word}' и выиграл "
                f"{game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    content=user_message,
                    current_time=guess_word_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.bot_nick,
                    content=message,
                    current_time=guess_word_dto.occurred_at,
                )
        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.user_name,
                    content=user_message,
                    current_time=guess_word_dto.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=guess_word_dto.channel_name,
                    user_name=guess_word_dto.bot_nick,
                    content=message,
                    current_time=guess_word_dto.occurred_at,
                )

        return message
