from collections import Counter

from sqlalchemy.orm import Session

from app.betting.domain.models import EmojiConfig, RarityLevel, BetRecord
from app.betting.domain.repo import BettingRepository
from app.economy.domain.economy_service import EconomyService


class BettingService:
    BET_COST = 50
    MIN_BET_AMOUNT = 10
    MAX_BET_AMOUNT = 100000

    JACKPOT_MULTIPLIER = 7
    PARTIAL_MULTIPLIER = 2

    RARITY_MULTIPLIERS = {
        RarityLevel.COMMON: 0.2,
        RarityLevel.UNCOMMON: 0.4,
        RarityLevel.RARE: 0.6,
        RarityLevel.EPIC: 1,
        RarityLevel.LEGENDARY: 5,
        RarityLevel.MYTHICAL: 100
    }

    CONSOLATION_PRIZES = {
        RarityLevel.MYTHICAL: 5000,
        RarityLevel.LEGENDARY: 50,
        RarityLevel.EPIC: 25,
        RarityLevel.RARE: 0,
        RarityLevel.UNCOMMON: 0,
        RarityLevel.COMMON: 0
    }

    def __init__(self, economy_service: EconomyService, repo: BettingRepository[Session]):
        self.economy_service = economy_service
        self._repo = repo

    def determine_correct_rarity(self, slot_result: str, result_type: str) -> RarityLevel:
        emojis = EmojiConfig.parse_slot_result(slot_result)

        if result_type == "jackpot":
            return EmojiConfig.get_emoji_rarity(emojis[0])

        rarity_priority = {
            RarityLevel.COMMON: 1,
            RarityLevel.UNCOMMON: 2,
            RarityLevel.RARE: 3,
            RarityLevel.EPIC: 4,
            RarityLevel.LEGENDARY: 5,
            RarityLevel.MYTHICAL: 6
        }

        if result_type == "partial":
            counts = Counter(emojis)
            repeated_emoji = next((emoji for emoji, count in counts.items() if count == 2), None)
            unique_emoji = next((emoji for emoji, count in counts.items() if count == 1), None)

            repeated_rarity = EmojiConfig.get_emoji_rarity(repeated_emoji)
            unique_rarity = EmojiConfig.get_emoji_rarity(unique_emoji) if unique_emoji else RarityLevel.COMMON

            return repeated_rarity if rarity_priority[repeated_rarity] >= rarity_priority[unique_rarity] else unique_rarity
        else:
            rarities = [EmojiConfig.get_emoji_rarity(emoji) for emoji in emojis]
            max_rarity = max(rarities, key=lambda r: rarity_priority[r])
            return max_rarity

    def save_bet(self, db: Session, channel_name: str, user_name: str, slot_result: str, result_type: str, rarity_level: RarityLevel):
        self._repo.save_bet_history(db, channel_name, user_name, slot_result, result_type, rarity_level)

    def get_user_bets(self, db: Session, channel_name: str, user_name: str) -> list[BetRecord]:
        return self._repo.get_user_bets(db, channel_name, user_name)
