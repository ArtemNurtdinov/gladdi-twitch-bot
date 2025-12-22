import random
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.minigame.domain.models import GuessNumberGame, WordGuessGame, RPSGame, RPS_CHOICES
from app.minigame.domain.repo import WordHistoryRepository

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

    def __init__(self, word_history_repo: WordHistoryRepository[Session]):
        self.word_history_repo = word_history_repo
        self.active_guess_games: Dict[str, GuessNumberGame] = {}
        self.active_word_games: Dict[str, WordGuessGame] = {}
        self.active_rps_games: Dict[str, RPSGame] = {}
        self.last_game_time: Dict[str, datetime] = {}
        self.stream_start_time: Dict[str, datetime] = {}

    def set_stream_start_time(self, channel_name: str, start_time: datetime):
        self.stream_start_time[channel_name] = start_time

    def reset_stream_state(self, channel_name: str):
        if channel_name in self.stream_start_time:
            del self.stream_start_time[channel_name]

        if channel_name in self.active_guess_games:
            self.finish_guess_game_timeout(channel_name)
        if channel_name in self.active_word_games:
            self.finish_word_game_timeout(channel_name)
        if channel_name in self.active_rps_games:
            game = self.get_active_rps_game(channel_name)
            self.finish_rps(game, channel_name)

    def should_start_new_game(self, channel_name: str) -> bool:
        if channel_name in self.active_guess_games or channel_name in self.active_word_games or channel_name in self.active_rps_games:
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

        self.active_guess_games[channel_name] = game
        self.last_game_time[channel_name] = start_time

        return game

    def is_game_active(self, channel_name: str) -> bool:
        return True if channel_name in self.active_guess_games else False

    def get_active_game(self, channel_name: str) -> GuessNumberGame:
        return self.active_guess_games[channel_name]

    def finish_game_with_winner(self, game: GuessNumberGame, channel_name: str, winner_name: str, winning_number: int):
        game.is_active = False
        game.winner = winner_name
        game.winning_time = datetime.utcnow()
        del self.active_guess_games[channel_name]

    def finish_guess_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_guess_games:
            return "Игра не найдена"

        game = self.active_guess_games[channel_name]
        game.is_active = False

        timeout_message = f"Время игры 'угадай число' истекло! Загаданное число было {game.target_number}. Никто не выиграл на этот раз."

        logger.info(f"Игра 'угадай число' завершена по таймауту. Число: {game.target_number}")

        del self.active_guess_games[channel_name]

        return timeout_message

    def check_rps_game_complete_time(self, channel_name: str, current_time: datetime) -> bool:
        if channel_name not in self.active_rps_games:
            return False

        game = self.active_rps_games.get(channel_name)
        if current_time > game.end_time and game.is_active:
            return True

        return False

    def check_expired_games(self) -> Dict[str, str]:
        expired_messages: Dict[str, str] = {}

        for channel_name in list(self.active_guess_games.keys()):
            game = self.active_guess_games.get(channel_name)
            if game and datetime.utcnow() > game.end_time and game.is_active:
                timeout_message = self.finish_guess_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        for channel_name in list(self.active_word_games.keys()):
            game = self.active_word_games.get(channel_name)
            if game and datetime.utcnow() > game.end_time and game.is_active:
                timeout_message = self.finish_word_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        return expired_messages

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

    def is_word_game_active(self, channel_name) -> bool:
        return True if channel_name in self.active_word_games else False

    def get_active_word_game(self, channel_name: str) -> WordGuessGame:
        return self.active_word_games[channel_name]

    def get_word_game_status(self, channel_name: str) -> Optional[str]:
        if channel_name not in self.active_word_games:
            return None
        game = self.active_word_games[channel_name]
        if datetime.utcnow() > game.end_time:
            return self.finish_word_game_timeout(channel_name)

        if game.winner:
            return f"Слово '{game.target_word}' угадал @{game.winner}! Выигрыш: {game.prize_amount} монет"
        elif not game.is_active:
            return f"Время истекло! Слово было '{game.target_word}'"
        else:
            letters_count = sum(1 for ch in game.target_word if ch.isalpha())
            return f"Угадайте слово из {letters_count} букв! Слово: {game.get_masked_word()}"

    def finish_word_game_with_winner(self, game: WordGuessGame, channel_name: str, winner_name: str):
        game.is_active = False
        game.winner = winner_name
        game.winning_time = datetime.utcnow()
        del self.active_word_games[channel_name]

    def finish_word_game_timeout(self, channel_name: str) -> str:
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

    def rps_game_is_active(self, channel_name: str) -> bool:
        return True if channel_name in self.active_rps_games else False

    def get_active_rps_game(self, channel_name: str) -> RPSGame:
        return self.active_rps_games[channel_name]

    def finish_rps(self, game: RPSGame, channel_name: str) -> tuple[str, str, list[str]]:
        bot_choice = random.choice(RPS_CHOICES)
        counter_map = {
            "камень": "бумага",
            "бумага": "ножницы",
            "ножницы": "камень",
        }
        winning_choice = counter_map[bot_choice]
        game.winner_choice = winning_choice
        winners = [user for user, choice in game.user_choices.items() if choice == game.winner_choice]
        del self.active_rps_games[channel_name]
        return bot_choice, winning_choice, winners

    def get_used_words(self, db: Session, channel_name: str, limit: int) -> list[str]:
        words = self.word_history_repo.list_recent_words(db, channel_name, limit)
        seen = set()
        unique_in_order = []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique_in_order.append(w)
        return unique_in_order

    def add_used_word(self, db: Session, channel_name: str, word: str) -> None:
        self.word_history_repo.add_word(db, channel_name, word)
