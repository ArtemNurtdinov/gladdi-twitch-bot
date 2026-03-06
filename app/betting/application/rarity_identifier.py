from app.betting.domain.model.rarity import RarityLevel
from app.betting.domain.models import EmojiConfig


class RarityIdentifier:
    def get_slot_result_rarity(self, result_type: str, emojis: list[str]) -> RarityLevel:
        if result_type == "jackpot":
            return EmojiConfig.get_emoji_rarity(emojis[0])

        rarity_priority = {
            RarityLevel.COMMON: 1,
            RarityLevel.UNCOMMON: 2,
            RarityLevel.RARE: 3,
            RarityLevel.EPIC: 4,
            RarityLevel.LEGENDARY: 5,
            RarityLevel.MYTHICAL: 6,
        }

        if result_type == "partial":
            repeated_emoji = max(set(emojis), key=emojis.count)
            unique_emoji = min(set(emojis), key=emojis.count)

            repeated_rarity = EmojiConfig.get_emoji_rarity(repeated_emoji)
            unique_rarity = EmojiConfig.get_emoji_rarity(unique_emoji)

            if rarity_priority[repeated_rarity] >= rarity_priority[unique_rarity]:
                max_rarity = repeated_rarity
            else:
                max_rarity = unique_rarity

            return max_rarity
        else:
            rarities = [EmojiConfig.get_emoji_rarity(emoji) for emoji in emojis]
            return max(rarities, key=lambda r: rarity_priority[r])
