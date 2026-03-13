from datetime import datetime

from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.domain.model.guess_number import GuessNumberGame
from app.minigame.domain.model.rps import RPSGame
from app.minigame.domain.model.word_guess import WordGuessGame

RPS_CHOICES = ("камень", "ножницы", "бумага")


class MinigameRepositoryImpl(MinigameRepository):
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

        guess_game = self.active_guess_games.get(channel_name)
        if guess_game:
            guess_game.is_active = False
            del self.active_guess_games[channel_name]

        word_game = self.active_word_games.get(channel_name)
        if word_game:
            word_game.is_active = False
            del self.active_word_games[channel_name]

        rps_game = self.get_active_rps_game(channel_name)
        if rps_game:
            rps_game.is_active = False
            del self.active_rps_games[channel_name]

    def get_last_game_time(self, channel_name: str) -> datetime | None:
        return self.last_game_time.get(channel_name)

    def get_stream_start_time(self, channel_name: str) -> datetime | None:
        return self.stream_start_time.get(channel_name)

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

    def save_active_rps_game(self, channel_name: str, game: RPSGame):
        self.active_rps_games[channel_name] = game
        self.last_game_time[channel_name] = game.start_time

    def delete_active_rps_game(self, channel_name: str):
        del self.active_rps_games[channel_name]
