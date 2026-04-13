from dataclasses import dataclass


@dataclass(frozen=True)
class BotConfig:
    prefix: str
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
