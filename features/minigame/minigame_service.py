import random
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from db.base import SessionLocal
from features.minigame.db.word_history import WordHistory
from features.minigame.models import GuessNumberGame, WordGuessGame, RPSGame, RPS_CHOICES
from features.economy.economy_service import EconomyService
from features.economy.db.transaction_history import TransactionType

logger = logging.getLogger(__name__)


class MinigameService:
    GUESS_GAME_DURATION_MINUTES = 5
    GUESS_GAME_PRIZE = 3000
    GUESS_MIN_NUMBER = 1
    GUESS_MAX_NUMBER = 100
    GUESS_PRIZE_DECREASE_PER_ATTEMPT = 100

    WORD_GAME_DURATION_MINUTES = 5
    WORD_GAME_MIN_PRIZE = 300
    WORD_GAME_MAX_PRIZE = 5000
    WORD_GAME_LETTER_REWARD_DECREASE = 200

    RPS_GAME_DURATION_MINUTES = 2
    RPS_BASE_BANK = 5000
    RPS_ENTRY_FEE_PER_USER = 50

    FIRST_GAME_START_MIN = 15
    FIRST_GAME_START_MAX = 30

    GAME_START_INTERVAL_MIN = 30
    GAME_START_INTERVAL_MAX = 60

    def __init__(self, economy_service: EconomyService):
        self.economy_service = economy_service
        self.active_games: Dict[str, GuessNumberGame] = {}
        self.active_word_games: Dict[str, WordGuessGame] = {}
        self.active_rps_games: Dict[str, RPSGame] = {}
        self.last_game_time: Dict[str, datetime] = {}
        self.stream_start_time: Dict[str, datetime] = {}

    def set_stream_start_time(self, channel_name: str, start_time: datetime):
        self.stream_start_time[channel_name] = start_time

    def reset_stream_state(self, channel_name: str):
        if channel_name in self.stream_start_time:
            del self.stream_start_time[channel_name]

        if channel_name in self.active_games:
            self._finish_game_timeout(channel_name)
        if channel_name in self.active_word_games:
            self._finish_word_game_timeout(channel_name)
        if channel_name in self.active_rps_games:
            self._finish_rps_timeout(channel_name)

    def should_start_new_game(self, channel_name: str) -> bool:
        if channel_name in self.active_games or channel_name in self.active_word_games or channel_name in self.active_rps_games:
            return False

        current_time = datetime.utcnow()

        if channel_name not in self.last_game_time:
            stream_start = self.stream_start_time[channel_name]
            time_since_stream_start = current_time - stream_start

            first_game_delay_minutes = random.randint(self.FIRST_GAME_START_MIN, self.FIRST_GAME_START_MAX)
            required_delay = timedelta(minutes=first_game_delay_minutes)

            logger.debug(f"Проверка первой игры для {channel_name}: прошло {time_since_stream_start}, нужно {required_delay}")
            return time_since_stream_start >= required_delay

        last_game_time = self.last_game_time[channel_name]
        time_since_last = current_time - last_game_time

        random_minutes = random.randint(self.GAME_START_INTERVAL_MIN, self.GAME_START_INTERVAL_MAX)
        required_interval = timedelta(minutes=random_minutes)

        logger.debug(f"Проверка следующей игры для {channel_name}: прошло {time_since_last}, нужно {required_interval}")
        return time_since_last >= required_interval

    def start_guess_number_game(self, channel_name: str) -> GuessNumberGame:
        target_number = random.randint(self.GUESS_MIN_NUMBER, self.GUESS_MAX_NUMBER)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.GUESS_GAME_DURATION_MINUTES)

        game = GuessNumberGame(
            channel_name=channel_name,
            target_number=target_number,
            start_time=start_time,
            end_time=end_time,
            min_number=self.GUESS_MIN_NUMBER,
            max_number=self.GUESS_MAX_NUMBER,
            prize_amount=self.GUESS_GAME_PRIZE
        )

        self.active_games[channel_name] = game
        self.last_game_time[channel_name] = start_time

        return game

    def process_guess(self, channel_name: str, user_name: str, guess: int) -> tuple[bool, str]:
        if channel_name not in self.active_games:
            return False, "Сейчас нет активной игры 'угадай число'"

        game = self.active_games[channel_name]

        if datetime.utcnow() > game.end_time:
            self._finish_game_timeout(channel_name)
            return False, f"Время игры истекло! Загаданное число было {game.target_number}"

        if not game.is_active:
            return False, "Игра уже завершена"

        if not game.min_number <= guess <= game.max_number:
            return False, f"Число должно быть от {game.min_number} до {game.max_number}"

        if guess == game.target_number:
            return self._finish_game_with_winner(channel_name, user_name, guess)
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - self.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            return False, f"@{user_name}, не угадал! Загаданное число {hint} {guess}."

    def _finish_game_with_winner(self, channel_name: str, winner_name: str, winning_number: int) -> tuple[bool, str]:
        game = self.active_games[channel_name]
        game.is_active = False
        game.winner = winner_name
        game.winning_time = datetime.utcnow()

        try:
            description = f"Победа в игре 'угадай число': {winning_number}"
            winner_balance = self.economy_service.add_balance(channel_name, winner_name, game.prize_amount, TransactionType.MINIGAME_WIN, description)

            success_message = f"ПОЗДРАВЛЯЕМ! @{winner_name} угадал число {winning_number} и выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            logger.info(f"Игра 'угадай число' завершена в канале {channel_name}. Победитель: {winner_name}, число: {winning_number}, приз: {game.prize_amount}")

            del self.active_games[channel_name]

            return True, success_message

        except Exception as e:
            logger.error(f"Ошибка при начислении приза победителю {winner_name}: {e}")
            game.is_active = False
            del self.active_games[channel_name]
            return False, f"❌ Ошибка при начислении приза. Игра завершена."

    def _finish_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_games:
            return "Игра не найдена"

        game = self.active_games[channel_name]
        game.is_active = False

        timeout_message = f"Время игры 'угадай число' истекло! Загаданное число было {game.target_number}. Никто не выиграл на этот раз."

        logger.info(f"Игра 'угадай число' завершена по таймауту. Число: {game.target_number}")

        del self.active_games[channel_name]

        return timeout_message

    def check_expired_games(self) -> Dict[str, str]:
        expired_messages: Dict[str, str] = {}

        for channel_name in list(self.active_games.keys()):
            game = self.active_games.get(channel_name)
            if game and datetime.utcnow() > game.end_time and game.is_active:
                timeout_message = self._finish_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        for channel_name in list(self.active_word_games.keys()):
            game = self.active_word_games.get(channel_name)
            if game and datetime.utcnow() > game.end_time and game.is_active:
                timeout_message = self._finish_word_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        for channel_name in list(self.active_rps_games.keys()):
            game = self.active_rps_games.get(channel_name)
            if game and datetime.utcnow() > game.end_time and game.is_active:
                timeout_message = self._finish_rps_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        return expired_messages

    def get_game_status(self, channel_name: str) -> Optional[str]:
        if channel_name not in self.active_games:
            return None

        game = self.active_games[channel_name]

        if datetime.utcnow() > game.end_time:
            return self._finish_game_timeout(channel_name)

        if game.winner:
            return f"Число {game.target_number} угадал @{game.winner}! Выигрыш: {game.prize_amount} монет"
        elif not game.is_active:
            return f"Время истекло! Загаданное число было {game.target_number}"
        else:
            return f"Угадайте число от {game.min_number} до {game.max_number}! Приз: {game.prize_amount} монет."

    def force_end_game(self, channel_name: str) -> str:
        if channel_name not in self.active_games:
            return "Нет активной игры для завершения"

        return self._finish_game_timeout(channel_name)

    def start_word_guess_game(self, channel_name: str, word: str, hint: str) -> WordGuessGame:
        if channel_name in self.active_word_games:
            raise ValueError(f"Словесная игра уже активна в канале {channel_name}")

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.WORD_GAME_DURATION_MINUTES)
        game = WordGuessGame(channel_name, word, hint, start_time, end_time, prize_amount=self.WORD_GAME_MAX_PRIZE)
        self.active_word_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        logger.info(f"Запущена игра 'поле чудес' в канале {channel_name}. Слово: {word}, подсказка: {hint}")
        return game

    def process_letter(self, channel_name: str, user_name: str, letter: str) -> tuple[bool, str]:
        if channel_name not in self.active_word_games:
            return False, "Сейчас нет активной игры 'поле чудес'"

        game = self.active_word_games[channel_name]
        if datetime.utcnow() > game.end_time:
            self._finish_word_game_timeout(channel_name)
            return False, f"Время игры истекло! Слово было '{game.target_word}'"
        if not game.is_active:
            return False, "Игра уже завершена"
        if not len(letter) == 1 or not letter.isalpha():
            return False, "Введите одну букву русского алфавита"

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
                game.prize_amount = max(self.WORD_GAME_MIN_PRIZE, game.prize_amount - self.WORD_GAME_LETTER_REWARD_DECREASE)

            letters_in_word = {ch for ch in game.target_word if ch.isalpha()}
            all_letters_revealed = letters_in_word.issubset(game.guessed_letters)

            if all_letters_revealed:
                return self._finish_word_game_with_winner(channel_name, user_name)

            return False, f"Буква есть! Слово: {masked}."
        else:
            return False, f"Такой буквы нет. Слово: {masked}."

    def process_word(self, channel_name: str, user_name: str, word: str) -> tuple[bool, str]:
        if channel_name not in self.active_word_games:
            return False, "Сейчас нет активной игры 'поле чудес'"
        game = self.active_word_games[channel_name]
        if datetime.utcnow() > game.end_time:
            self._finish_word_game_timeout(channel_name)
            return False, f"Время игры истекло! Слово было '{game.target_word}'"
        if not game.is_active:
            return False, "Игра уже завершена"

        if word.strip().lower() == game.target_word:
            return self._finish_word_game_with_winner(channel_name, user_name)
        else:
            masked = game.get_masked_word()
            return False, f"Неверное слово. Слово: {masked}."

    def get_word_game_status(self, channel_name: str) -> Optional[str]:
        if channel_name not in self.active_word_games:
            return None
        game = self.active_word_games[channel_name]
        if datetime.utcnow() > game.end_time:
            return self._finish_word_game_timeout(channel_name)

        if game.winner:
            return f"Слово '{game.target_word}' угадал @{game.winner}! Выигрыш: {game.prize_amount} монет"
        elif not game.is_active:
            return f"Время истекло! Слово было '{game.target_word}'"
        else:
            letters_count = sum(1 for ch in game.target_word if ch.isalpha())
            return f"Угадайте слово из {letters_count} букв! Слово: {game.get_masked_word()}"


    def _finish_word_game_with_winner(self, channel_name: str, winner_name: str) -> tuple[bool, str]:
        game = self.active_word_games[channel_name]
        game.is_active = False
        game.winner = winner_name
        game.winning_time = datetime.utcnow()
        try:
            winner_balance = self.economy_service.add_balance(
                channel_name,
                winner_name,
                game.prize_amount,
                TransactionType.MINIGAME_WIN,
                f"Победа в игре 'поле чудес'"
            )
            success_message = (
                f"ПОЗДРАВЛЯЕМ! @{winner_name} угадал слово '{game.target_word}' и "
                f"выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            logger.info(
                f"Игра 'поле чудес' завершена. Победитель: {winner_name}, слово: {game.target_word}, приз: {game.prize_amount}"
            )
            del self.active_word_games[channel_name]
            return True, success_message
        except Exception as e:
            logger.error(f"Ошибка при начислении приза победителю {winner_name}: {e}")
            game.is_active = False
            del self.active_word_games[channel_name]
            return False, "Ошибка при начислении приза. Игра завершена."

    def _finish_word_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_word_games:
            return "Игра не найдена"
        game = self.active_word_games[channel_name]
        game.is_active = False
        timeout_message = f"Время игры 'поле чудес' истекло! Слово было '{game.target_word}'. Никто не выиграл."
        logger.info(f"Игра 'поле чудес' завершена по таймауту. Слово: {game.target_word}")
        del self.active_word_games[channel_name]
        return timeout_message

    def start_rps_game(self, channel_name: str) -> RPSGame:
        if channel_name in self.active_rps_games:
            raise ValueError(f"Игра 'камень-ножницы-бумага' уже активна в канале {channel_name}")
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.RPS_GAME_DURATION_MINUTES)
        game = RPSGame(channel_name=channel_name, start_time=start_time, end_time=end_time, bank=self.RPS_BASE_BANK)
        self.active_rps_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        logger.info(f"Запущена игра 'камень-ножницы-бумага' в канале {channel_name}")
        return game

    def join_rps(self, channel_name: str, user_name: str, choice: str) -> str:
        if channel_name not in self.active_rps_games:
            return "Сейчас нет активной игры 'камень-ножницы-бумага'"
        game = self.active_rps_games[channel_name]
        if datetime.utcnow() > game.end_time:
            self._finish_rps_timeout(channel_name)
            return "Время игры истекло!"
        if not game.is_active:
            return "Игра уже завершена"

        normalized_choice = choice.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            return "Выберите: камень, ножницы или бумага"

        normalized_user = user_name.lower()
        if normalized_user in game.user_choices:
            existing = game.user_choices[normalized_user]
            return f"Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"

        fee = self.RPS_ENTRY_FEE_PER_USER
        user_balance = self.economy_service.subtract_balance(channel_name, user_name, fee, TransactionType.SPECIAL_EVENT, "Участие в игре 'камень-ножницы-бумага'")
        if not user_balance:
            return f"Недостаточно средств! Требуется {fee} монет"

        normalized = user_name.lower()
        game.bank += fee
        game.user_choices[normalized] = choice

        return f"Принято: @{user_name} — {normalized_choice}. Участников: {len(game.user_choices)}"

    def finish_rps(self, channel_name: str) -> tuple[bool, str]:
        if channel_name not in self.active_rps_games:
            return False, "Игра не найдена"
        game = self.active_rps_games[channel_name]
        if not game.is_active:
            return False, "Игра уже завершена"

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
            for winner in winners:
                self.economy_service.add_balance(channel_name, winner, share, TransactionType.MINIGAME_WIN, f"Победа в КНБ ({winning_choice})")
            winners_display = ", ".join(f"@{winner}" for winner in winners)
            message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
        else:
            message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."

        game.is_active = False
        del self.active_rps_games[channel_name]
        logger.info(f"Игра 'камень-ножницы-бумага' завершена в канале {channel_name}: {message}")
        return True, message

    def _finish_rps_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_rps_games:
            return "Игра не найдена"
        success, message = self.finish_rps(channel_name)
        return message

    def get_used_words(self, channel_name: str, limit: int) -> list[str]:
        db = SessionLocal()
        try:
            q = db.query(WordHistory.word).filter(WordHistory.channel_name == channel_name).order_by(WordHistory.created_at.desc())
            if limit and limit > 0:
                q = q.limit(limit)
            rows = q.all()
            words = [row[0].lower() for row in rows]
            seen = set()
            unique_in_order = []
            for w in words:
                if w not in seen:
                    seen.add(w)
                    unique_in_order.append(w)
            return unique_in_order
        finally:
            db.close()

    def add_used_word(self, channel_name: str, word: str) -> None:
        normalized = "".join(ch for ch in str(word).lower() if ch.isalpha())
        if not normalized:
            return
        db = SessionLocal()
        try:
            record = WordHistory(channel_name=channel_name, word=normalized)
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
