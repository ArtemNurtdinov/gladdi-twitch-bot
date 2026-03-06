from app.betting.domain.model.rarity import RarityLevel


class EmojiConfig:
    EMOJI_SYSTEM = {
        "artemn3STUL": {"weight": 40, "rarity": RarityLevel.COMMON},
        "LUL": {"weight": 30, "rarity": RarityLevel.UNCOMMON},
        "artemn3SUDA": {"weight": 15, "rarity": RarityLevel.RARE},
        "artemn3BOSS": {"weight": 10, "rarity": RarityLevel.RARE},
        "artemn3Facepalm2": {"weight": 7, "rarity": RarityLevel.EPIC},
        "artemn3Chair": {"weight": 3, "rarity": RarityLevel.LEGENDARY},
        "DinoDance": {"weight": 0.001, "rarity": RarityLevel.MYTHICAL},
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
