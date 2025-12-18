from sqlalchemy.orm import Session

from features.betting.data.db.bet_history import BetHistory
from features.betting.domain.models import BetResult, EmojiConfig, RarityLevel
from features.economy.data.db.transaction_history import TransactionType
from features.economy.economy_service import EconomyService
from features.economy.domain.models import JackpotPayoutMultiplierEffect, PartialPayoutMultiplierEffect, MissPayoutMultiplierEffect
from features.equipment.model.user_equipment_item import UserEquipmentItem


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

    def __init__(self, economy_service: EconomyService):
        self.economy_service = economy_service

    def _determine_correct_rarity(self, slot_result: str, result_type: str) -> RarityLevel:
        emojis = EmojiConfig.parse_slot_result(slot_result)

        if result_type == "jackpot":
            return EmojiConfig.get_emoji_rarity(emojis[0])

        elif result_type == "partial":
            repeated_emoji = None
            for emoji in emojis:
                if emojis.count(emoji) == 2:
                    repeated_emoji = emoji
                    break

            if not repeated_emoji:
                return EmojiConfig.get_emoji_rarity(emojis[0])

            unique_emoji = None
            for emoji in emojis:
                if emojis.count(emoji) == 1:
                    unique_emoji = emoji
                    break

            repeated_rarity = EmojiConfig.get_emoji_rarity(repeated_emoji)
            unique_rarity = EmojiConfig.get_emoji_rarity(unique_emoji) if unique_emoji else RarityLevel.COMMON

            rarity_priority = {
                RarityLevel.COMMON: 1,
                RarityLevel.UNCOMMON: 2,
                RarityLevel.RARE: 3,
                RarityLevel.EPIC: 4,
                RarityLevel.LEGENDARY: 5,
                RarityLevel.MYTHICAL: 6
            }

            if rarity_priority[repeated_rarity] >= rarity_priority[unique_rarity]:
                return repeated_rarity
            else:
                return unique_rarity

        else:
            max_rarity = RarityLevel.COMMON
            for emoji in emojis:
                emoji_rarity = EmojiConfig.get_emoji_rarity(emoji)
                if emoji_rarity == RarityLevel.MYTHICAL:
                    max_rarity = RarityLevel.MYTHICAL
                    break
                elif emoji_rarity == RarityLevel.LEGENDARY and max_rarity != RarityLevel.MYTHICAL:
                    max_rarity = RarityLevel.LEGENDARY
                elif emoji_rarity == RarityLevel.EPIC and max_rarity not in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                    max_rarity = RarityLevel.EPIC
                elif emoji_rarity == RarityLevel.RARE and max_rarity not in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY, RarityLevel.EPIC]:
                    max_rarity = RarityLevel.RARE
                elif emoji_rarity == RarityLevel.UNCOMMON and max_rarity == RarityLevel.COMMON:
                    max_rarity = RarityLevel.UNCOMMON
            return max_rarity

    def process_bet_result_with_amount(self, db: Session, channel_name: str, user_name: str, result_type: str, slot_result: str, bet_amount: int,
                                       equipment: list[UserEquipmentItem]) -> BetResult:
        if bet_amount < self.MIN_BET_AMOUNT:
            return BetResult.failure_result(f"Минимальная сумма ставки: {self.MIN_BET_AMOUNT} монет. Указано: {bet_amount} монет.", bet_amount)

        if bet_amount > self.MAX_BET_AMOUNT:
            return BetResult.failure_result(f"Максимальная сумма ставки: {self.MAX_BET_AMOUNT} монет. Указано: {bet_amount} монет.", bet_amount)

        rarity_level = self._determine_correct_rarity(slot_result, result_type)
        user_balance = self.economy_service.subtract_balance(db, channel_name, user_name, bet_amount, TransactionType.BET_LOSS, f"Ставка в слот-машине: {slot_result}")

        if not user_balance:
            return BetResult.failure_result(f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет.", bet_amount)

        base_payout = self.RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
        timeout_seconds = None

        if result_type == "jackpot":
            payout = base_payout * self.JACKPOT_MULTIPLIER
        elif result_type == "partial":
            payout = base_payout * self.PARTIAL_MULTIPLIER
        else:
            consolation_prize = self.CONSOLATION_PRIZES.get(rarity_level, 0)
            if consolation_prize > 0:
                payout = max(consolation_prize, bet_amount * 0.1)
                if rarity_level in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                    timeout_seconds = 0
                elif rarity_level == RarityLevel.EPIC:
                    timeout_seconds = 60
                else:
                    timeout_seconds = 120
            else:
                payout = 0
                timeout_seconds = 180

        if payout > 0:
            if result_type in ("jackpot", "partial"):
                jackpot_multiplier = 1.0
                partial_multiplier = 1.0
                for item in equipment:
                    for effect in item.shop_item.effects:
                        if isinstance(effect, JackpotPayoutMultiplierEffect) and result_type == "jackpot":
                            jackpot_multiplier *= effect.multiplier
                        if isinstance(effect, PartialPayoutMultiplierEffect) and result_type == "partial":
                            partial_multiplier *= effect.multiplier
                if result_type == "jackpot" and jackpot_multiplier != 1.0:
                    payout *= jackpot_multiplier
                if result_type == "partial" and partial_multiplier != 1.0:
                    payout *= partial_multiplier
            elif result_type == "miss":
                miss_multiplier = 1.0
                for item in equipment:
                    for effect in item.shop_item.effects:
                        if isinstance(effect, MissPayoutMultiplierEffect):
                            miss_multiplier *= effect.multiplier
                if miss_multiplier != 1.0:
                    payout *= miss_multiplier

        payout = int(payout) if payout > 0 else 0

        if payout > 0:
            transaction_type = TransactionType.BET_WIN if result_type != "miss" else TransactionType.BET_WIN
            description = f"Выигрыш в слот-машине: {slot_result}" if result_type != "miss" else f"Консольный приз: {slot_result}"
            user_balance = self.economy_service.add_balance(db, channel_name, user_name, payout, transaction_type, description)

        return BetResult.success_result(bet_amount, payout, user_balance.balance, result_type, rarity_level, timeout_seconds)

    def save_bet_history(self, db: Session, channel_name: str, user_name: str, slot_result: str, result_type: str, rarity_level: RarityLevel):
        normalized_user_name = user_name.lower()
        bet = BetHistory(channel_name=channel_name, user_name=normalized_user_name, slot_result=slot_result, result_type=result_type, rarity_level=rarity_level)
        db.add(bet)

    def get_user_bets(self, db: Session, channel_name: str, user_name: str) -> list[BetHistory]:
        return db.query(BetHistory).filter(BetHistory.user_name == user_name).filter(BetHistory.channel_name == channel_name).all()
