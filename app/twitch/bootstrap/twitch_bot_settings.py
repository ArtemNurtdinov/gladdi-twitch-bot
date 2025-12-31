from dataclasses import dataclass

from core.config import config


@dataclass(frozen=True)
class TwitchBotSettings:
    channel_name: str = "artemnefrit"
    prefix: str = "!"
    group_id: int = config.telegram.group_id
    check_viewers_interval_seconds: int = 10
    check_stream_status_interval_seconds: int = 60
    sync_followers_interval_seconds: int = 24 * 60 * 60
    command_roll: str = "ставка"
    command_followage: str = "followage"
    command_gladdi: str = "gladdi"
    command_fight: str = "битва"
    command_balance: str = "баланс"
    command_bonus: str = "бонус"
    command_transfer: str = "перевод"
    command_shop: str = "магазин"
    command_buy: str = "купить"
    command_equipment: str = "экипировка"
    command_top: str = "топ"
    command_bottom: str = "бомжи"
    command_stats: str = "стата"
    command_guess: str = "угадай"
    command_guess_letter: str = "буква"
    command_guess_word: str = "слово"
    command_rps: str = "кнб"
    command_help: str = "команды"


DEFAULT_SETTINGS = TwitchBotSettings()
