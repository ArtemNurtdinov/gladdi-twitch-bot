from app.betting.application.rarity_identifier import RarityIdentifier
from app.betting.domain.model.bet import Bet
from app.betting.domain.model.rarity import RarityLevel
from app.betting.domain.models import EmojiConfig
from app.betting.domain.repo import BettingRepository


class BettingService:
    BET_COST = 50
    MIN_BET_AMOUNT = 10
    MAX_BET_AMOUNT = 100000

    JACKPOT_MULTIPLIER = 8
    PARTIAL_MULTIPLIER = 2

    RARITY_MULTIPLIERS = {
        RarityLevel.COMMON: 0.2,
        RarityLevel.UNCOMMON: 0.4,
        RarityLevel.RARE: 0.6,
        RarityLevel.EPIC: 1,
        RarityLevel.LEGENDARY: 5,
        RarityLevel.MYTHICAL: 100,
    }

    def __init__(self, repo: BettingRepository, rarity_identifier: RarityIdentifier):
        self._repo = repo
        self._rarity_identifier = rarity_identifier

    def determine_correct_rarity(self, slot_result: str, result_type: str) -> RarityLevel:
        emojis = EmojiConfig.parse_slot_result(slot_result)
        return self._rarity_identifier.get_slot_result_rarity(result_type, emojis)

    def save_bet(self, channel_name: str, user_name: str, slot_result: str, result_type: str, rarity_level: RarityLevel):
        self._repo.save_bet_history(channel_name, user_name, slot_result, result_type, rarity_level)

    def get_user_bets(self, channel_name: str, user_name: str) -> list[Bet]:
        return self._repo.get_user_bets(channel_name, user_name)
