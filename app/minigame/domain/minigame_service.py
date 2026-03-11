import random
from datetime import datetime, timedelta

from app.minigame.domain.model.guess_number import GuessNumberGame
from app.minigame.domain.model.rps import RPSGame
from app.minigame.domain.model.word_guess import WordGuessGame

RPS_CHOICES = ("камень", "ножницы", "бумага")


class MinigameService:
    GUESS_GAME_DURATION_MINUTES = 5
    GUESS_GAME_PRIZE = 3000
    GUESS_MIN_NUMBER = 1
    GUESS_MAX_NUMBER = 100
    GUESS_PRIZE_DECREASE_PER_ATTEMPT = 100

    WORD_GAME_DURATION_MINUTES = 5
    WORD_GAME_MIN_PRIZE = 300
    WORD_GAME_MAX_PRIZE = 2000
    WORD_GAME_LETTER_REWARD_DECREASE = 200

    RPS_GAME_DURATION_MINUTES = 2
    RPS_BASE_BANK = 1500
    RPS_ENTRY_FEE_PER_USER = 100

    FIRST_GAME_START_MIN = 15
    FIRST_GAME_START_MAX = 30

    GAME_START_INTERVAL_MIN = 30
    GAME_START_INTERVAL_MAX = 60

    def __init__(self):
        self.active_guess_games: dict[str, GuessNumberGame] = {}
        self.active_word_games: dict[str, WordGuessGame] = {}
        self.active_rps_games: dict[str, RPSGame] = {}
        self.last_game_time: dict[str, datetime] = {}
        self.stream_start_time: dict[str, datetime] = {}

    def set_stream_start_time(self, channel_name: str, start_time: datetime):
        self.stream_start_time[channel_name] = start_time
        print(f"set_stream_start_time for {channel_name}: {start_time}")

    def reset_stream_state(self, channel_name: str):
        if channel_name in self.stream_start_time:
            del self.stream_start_time[channel_name]

        if channel_name in self.active_guess_games:
            game = self.active_guess_games[channel_name]
            game.is_active = False
            del self.active_guess_games[channel_name]
        if channel_name in self.active_word_games:
            self.finish_word_game_timeout(channel_name)

        rps_game = self.get_active_rps_game(channel_name)
        if rps_game:
            self.finish_rps(rps_game, channel_name)

    def should_start_new_game(self, channel_name: str) -> bool:
        if channel_name in self.active_guess_games or channel_name in self.active_word_games or channel_name in self.active_rps_games:
            return False

        current_time = datetime.utcnow()

        if channel_name not in self.last_game_time:
            stream_start = self.stream_start_time[channel_name]
            time_since_stream_start = current_time - stream_start

            first_game_delay_minutes = random.randint(self.FIRST_GAME_START_MIN, self.FIRST_GAME_START_MAX)
            required_delay = timedelta(minutes=first_game_delay_minutes)

            return time_since_stream_start >= required_delay

        last_game_time = self.last_game_time[channel_name]
        time_since_last = current_time - last_game_time

        print(f"last_game_time = {last_game_time}, current_time = {current_time}, time_since_last = {time_since_last}")

        random_minutes = random.randint(self.GAME_START_INTERVAL_MIN, self.GAME_START_INTERVAL_MAX)
        required_interval = timedelta(minutes=random_minutes)

        return time_since_last >= required_interval

    def start_guess_number_game(self, channel_name: str) -> GuessNumberGame:
        if channel_name in self.active_guess_games:
            raise ValueError(f"Игра уже активна в канале {channel_name}")

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
            prize_amount=self.GUESS_GAME_PRIZE,
        )

        self.active_guess_games[channel_name] = game
        self.last_game_time[channel_name] = start_time

        return game

    def delete_guess_number_game(self, channel_name: str):
        del self.active_guess_games[channel_name]

    def delete_guess_game(self, channel_name: str):
        del self.active_guess_games[channel_name]

    def get_active_rps_game(self, channel_name: str) -> RPSGame | None:
        return self.active_rps_games.get(channel_name)

    def get_active_guess_game(self, channel_name: str) -> GuessNumberGame | None:
        return self.active_guess_games.get(channel_name)

    def get_active_word_game(self, channel_name: str) -> WordGuessGame | None:
        return self.active_word_games.get(channel_name)

    def save_word_gues_game(self, channel_name: str, game: WordGuessGame):
        self.active_word_games[channel_name] = game
        self.last_game_time[channel_name] = game.start_time

    def delete_word_guess_game(self, channel_name: str):
        del self.active_word_games[channel_name]

    def finish_word_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_word_games:
            return "Игра не найдена"
        game = self.active_word_games[channel_name]
        game.is_active = False
        timeout_message = f"Время игры 'поле чудес' истекло! Слово было '{game.target_word}'. Никто не выиграл."
        del self.active_word_games[channel_name]
        return timeout_message

    def start_rps_game(self, channel_name: str) -> RPSGame:
        if channel_name in self.active_rps_games:
            raise ValueError(f"Игра 'камень-ножницы-бумага' уже активна в канале {channel_name}")
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.RPS_GAME_DURATION_MINUTES)
        game = RPSGame(
            channel_name=channel_name,
            start_time=start_time,
            end_time=end_time,
            bank=self.RPS_BASE_BANK,
            is_active=True,
            winner_choice=None,
            user_choices={},
        )
        self.active_rps_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        return game

    def rps_game_is_active(self, channel_name: str) -> bool:
        return True if channel_name in self.active_rps_games else False

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
