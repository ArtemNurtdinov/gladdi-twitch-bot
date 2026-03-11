import random
from datetime import datetime

from app.minigame.domain.model.guess_number import GuessNumberGame
from app.minigame.domain.model.rps import RPSGame
from app.minigame.domain.model.word_guess import WordGuessGame

RPS_CHOICES = ("камень", "ножницы", "бумага")


class MinigameService:
    RPS_ENTRY_FEE_PER_USER = 100

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

        guess_game = self.active_guess_games[channel_name]
        if guess_game:
            guess_game.is_active = False
            del self.active_guess_games[channel_name]

        if channel_name in self.active_word_games:
            self.finish_word_game_timeout(channel_name)

        rps_game = self.get_active_rps_game(channel_name)

        if rps_game:
            self.finish_rps(rps_game, channel_name)

    def get_last_game_time(self, channel_name: str) -> datetime | None:
        return self.last_game_time[channel_name]

    def get_stream_start_time(self, channel_name: str) -> datetime | None:
        return self.stream_start_time[channel_name]

    def save_active_guess_number_game(self, channel_name: str, game: GuessNumberGame):
        self.active_guess_games[channel_name] = game
        self.last_game_time[channel_name] = game.start_time

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

    def save_active_rps_game(self, channel_name: str, game: RPSGame):
        self.active_rps_games[channel_name] = game
        self.last_game_time[channel_name] = game.start_time

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
