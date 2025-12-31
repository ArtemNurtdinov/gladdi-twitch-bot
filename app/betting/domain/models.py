from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class BetRecord:
    id: int
    channel_name: str
    user_name: str
    slot_result: str
    result_type: str
    rarity_level: "RarityLevel"
    created_at: datetime


class RarityLevel(Enum):
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"
    MYTHICAL = "MYTHICAL"


class EmojiConfig:
    EMOJI_SYSTEM = {
        "artemn3STUL": {"rank": 1, "weight": 40, "rarity": RarityLevel.COMMON},
        "LUL": {"rank": 2, "weight": 30, "rarity": RarityLevel.UNCOMMON},
        "artemn3BOSS": {"rank": 3, "weight": 20, "rarity": RarityLevel.RARE},
        "artemn3Facepalm2": {"rank": 4, "weight": 7, "rarity": RarityLevel.EPIC},
        "artemn3Chair": {"rank": 5, "weight": 3, "rarity": RarityLevel.LEGENDARY},
        "DinoDance": {"rank": 6, "weight": 0.0001, "rarity": RarityLevel.MYTHICAL},
    }

    @classmethod
    def get_emoji_rarity(cls, emoji_name: str) -> RarityLevel:
        return cls.EMOJI_SYSTEM.get(emoji_name, {}).get("rarity", RarityLevel.COMMON)

    @classmethod
    def get_emoji_weight(cls, emoji_name: str) -> float:
        return cls.EMOJI_SYSTEM.get(emoji_name, {}).get("weight", 1.0)

    @classmethod
    def get_emojis_list(cls) -> list[str]:
        return list(cls.EMOJI_SYSTEM.keys())

    @classmethod
    def get_weights_list(cls) -> list[float]:
        return [cls.EMOJI_SYSTEM[emoji]["weight"] for emoji in cls.get_emojis_list()]

    @classmethod
    def parse_slot_result(cls, slot_result: str) -> list[str]:
        return [emoji.strip() for emoji in slot_result.split("|")]

    @classmethod
    def format_slot_result(cls, emojis: list[str]) -> str:
        return " | ".join(emojis)

    @classmethod
    def get_emoji_rarities_dict(cls) -> dict[str, RarityLevel]:
        return {emoji: data["rarity"] for emoji, data in cls.EMOJI_SYSTEM.items()}
