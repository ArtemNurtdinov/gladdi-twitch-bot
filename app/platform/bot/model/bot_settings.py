from dataclasses import dataclass

from core.config import Config


@dataclass(frozen=True)
class BotSettings:
    group_id: int
    channel_name: str
    bot_name: str
    prefix: str
    check_viewers_interval_seconds: int
    check_stream_status_interval_seconds: int
    sync_followers_interval_seconds: int
    command_roll: str
    command_followage: str
    command_gladdi: str
    command_fight: str
    command_balance: str
    command_bonus: str
    command_transfer: str
    command_shop: str
    command_buy: str
    command_equipment: str
    command_top: str
    command_bottom: str
    command_stats: str
    command_guess: str
    command_guess_letter: str
    command_guess_word: str
    command_rps: str
    command_help: str


@dataclass(frozen=True)
class DefaultBotSettings(BotSettings):
    group_id: int
    channel_name: str = "artemnefrit"
    bot_name: str = "gladdi_bot"
    prefix: str = "!"
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


def build_bot_settings(cfg: Config) -> BotSettings:
    group_id = cfg.telegram.group_id
    settings = DefaultBotSettings(group_id=group_id)
    return settings
