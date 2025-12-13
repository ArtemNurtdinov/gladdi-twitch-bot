import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from db.base import SessionLocal
from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory, TransactionType
from features.equipment.model.user_equipment_item import UserEquipmentItem
from features.betting.model.rarity_level import RarityLevel
from features.economy.model.user_stats import UserStats
from features.economy.model.bet_result import BetResult
from features.betting.model.emoji_config import EmojiConfig
from features.economy.model.transfer_result import TransferResult
from features.economy.model.shop_items import ShopItems, ShopItemType, DailyBonusMultiplierEffect, TimeoutProtectionEffect, TimeoutReductionEffect, \
    RollCooldownOverrideEffect, JackpotPayoutMultiplierEffect, PartialPayoutMultiplierEffect, MissPayoutMultiplierEffect
from features.equipment.db.user_equipment import UserEquipment
from features.stream.stream_service import StreamService

logger = logging.getLogger(__name__)


@dataclass
class DailyBonusResult:
    success: bool
    user_balance: Optional[UserBalance] = None
    bonus_amount: int = 0
    bonus_message: str = ""
    failure_reason: str = ""


class EconomyService:
    STARTING_BALANCE = 1000
    DAILY_BONUS = 200

    BET_COST = 50
    MIN_BET_AMOUNT = 10
    MAX_BET_AMOUNT = 100000

    ACTIVITY_MESSAGES_REQUIRED = 1
    ACTIVITY_REWARD = 10
    ACTIVITY_COOLDOWN_MINUTES = 10

    RARITY_MULTIPLIERS = {
        RarityLevel.COMMON: 0.2,
        RarityLevel.UNCOMMON: 0.4,
        RarityLevel.RARE: 0.6,
        RarityLevel.EPIC: 1,
        RarityLevel.LEGENDARY: 5,
        RarityLevel.MYTHICAL: 100
    }

    JACKPOT_MULTIPLIER = 7
    PARTIAL_MULTIPLIER = 2

    CONSOLATION_PRIZES = {
        RarityLevel.MYTHICAL: 5000,
        RarityLevel.LEGENDARY: 50,
        RarityLevel.EPIC: 25,
        RarityLevel.RARE: 0,
        RarityLevel.UNCOMMON: 0,
        RarityLevel.COMMON: 0
    }

    BATTLE_ENTRY_FEE = 100
    BATTLE_WINNER_PRIZE = 200

    def __init__(self, stream_service: StreamService):
        self.stream_service = stream_service

    def process_user_message_activity(self, channel_name: str, user_name: str) -> Optional[UserBalance]:
        db = SessionLocal()
        try:
            user_balance = self.get_user_balance(channel_name, user_name)
            user_balance = db.merge(user_balance)

            user_balance.message_count += 1
            user_balance.updated_at = datetime.utcnow()

            if self._should_grant_activity_reward(user_balance):
                user_balance.last_activity_reward = datetime.utcnow()

                balance_before = user_balance.balance
                user_balance.balance += self.ACTIVITY_REWARD
                user_balance.total_earned += self.ACTIVITY_REWARD

                self._create_transaction(db, channel_name, user_name, TransactionType.MESSAGE_REWARD, self.ACTIVITY_REWARD, balance_before, user_balance.balance,
                                         "Награда за активность в чате")

                db.commit()
                logger.info(f"Пользователь {user_name} получил {self.ACTIVITY_REWARD} монет за активность. Новый баланс: {user_balance.balance}")

                db.refresh(user_balance)
                return user_balance
            else:
                db.commit()
                return None

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обработке активности пользователя {user_name}: {e}")
            return None
        finally:
            db.close()

    def _should_grant_activity_reward(self, user_balance: UserBalance) -> bool:
        if user_balance.last_activity_reward is not None:
            time_since_last = datetime.utcnow() - user_balance.last_activity_reward
            if time_since_last < timedelta(minutes=self.ACTIVITY_COOLDOWN_MINUTES):
                logger.debug(f"{user_balance.user_name} в кулдауне активности. Осталось: {self.ACTIVITY_COOLDOWN_MINUTES * 60 - time_since_last.total_seconds():.0f} сек")
                return False

        return True

    def user_exists(self, channel_name: str, user_name: str) -> bool:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            user_balance = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .first()
            )
            return user_balance is not None
        finally:
            db.close()

    def get_user_balance(self, channel_name: str, user_name: str) -> UserBalance:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            user_balance = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .first()
            )

            if not user_balance:
                user_balance = UserBalance(channel_name=channel_name, user_name=normalized_user_name, balance=self.STARTING_BALANCE)
                db.add(user_balance)

                self._create_transaction(db, channel_name, normalized_user_name, TransactionType.ADMIN_ADJUST, self.STARTING_BALANCE, 0, self.STARTING_BALANCE,
                                         "Создание нового аккаунта")

                db.commit()
                logger.info(f"Создан новый пользователь {normalized_user_name} с балансом {self.STARTING_BALANCE}")

            db.refresh(user_balance)

            return user_balance
        finally:
            db.close()

    def add_balance(self, channel_name: str, user_name: str, amount: int, transaction_type: TransactionType, description: str = None) -> UserBalance:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            user_balance = self.get_user_balance(channel_name, user_name)
            user_balance = db.merge(user_balance)

            balance_before = user_balance.balance or 0
            user_balance.balance = (user_balance.balance or 0) + amount
            user_balance.total_earned = (user_balance.total_earned or 0) + max(0, amount)
            user_balance.updated_at = datetime.utcnow()

            self._create_transaction(db, channel_name, normalized_user_name, transaction_type, amount, balance_before, user_balance.balance, description)

            db.commit()
            logger.info(f"Пользователю {normalized_user_name} добавлено {amount} монет. Новый баланс: {user_balance.balance}")

            db.refresh(user_balance)
            return user_balance
        finally:
            db.close()

    def add_balance_with_session(self, db: Session, channel_name: str, user_name: str, amount: int, transaction_type: TransactionType, description: str = None):
        normalized_user_name = user_name.lower()

        user_balance = (
            db.query(UserBalance)
            .filter_by(channel_name=channel_name, user_name=normalized_user_name)
            .first()
        )

        if not user_balance:
            user_balance = UserBalance(channel_name=channel_name, user_name=normalized_user_name, balance=self.STARTING_BALANCE)
            db.add(user_balance)

            self._create_transaction(db, channel_name, normalized_user_name, TransactionType.ADMIN_ADJUST, self.STARTING_BALANCE, 0,
                                     self.STARTING_BALANCE, "Создание нового аккаунта")
            logger.info(f"Создан новый пользователь {normalized_user_name} с балансом {self.STARTING_BALANCE}")

        balance_before = user_balance.balance or 0
        user_balance.balance = (user_balance.balance or 0) + amount
        user_balance.total_earned = (user_balance.total_earned or 0) + max(0, amount)
        user_balance.updated_at = datetime.utcnow()

        self._create_transaction(db, channel_name, normalized_user_name, transaction_type, amount, balance_before, user_balance.balance, description)

        logger.info(f"Пользователю {normalized_user_name} добавлено {amount} монет. Новый баланс: {user_balance.balance}")

    def subtract_balance(self, channel_name: str, user_name: str, amount: int, transaction_type: TransactionType, description: str = None) -> Optional[UserBalance]:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            user_balance = self.get_user_balance(channel_name, user_name)
            user_balance = db.merge(user_balance)

            current_balance = user_balance.balance or 0
            if current_balance < amount:
                logger.warning(f"Недостаточно средств у {normalized_user_name}: {current_balance} < {amount}")
                return None

            balance_before = current_balance
            user_balance.balance = current_balance - amount
            user_balance.total_spent = (user_balance.total_spent or 0) + amount
            user_balance.updated_at = datetime.utcnow()

            self._create_transaction(db, channel_name, normalized_user_name, transaction_type, -amount, balance_before, user_balance.balance, description)

            db.commit()
            logger.info(f"У пользователя {normalized_user_name} списано {amount} монет. Новый баланс: {user_balance.balance}")

            db.refresh(user_balance)

            return user_balance
        finally:
            db.close()

    def transfer_money(self, channel_name: str, sender_name: str, receiver_name: str, amount: int) -> TransferResult:
        MIN_TRANSFER_AMOUNT = 100
        if amount < MIN_TRANSFER_AMOUNT:
            return TransferResult.failure_result(f"Минимальная сумма перевода: {MIN_TRANSFER_AMOUNT} монет", amount)

        MAX_TRANSFER_AMOUNT = 5000
        if amount > MAX_TRANSFER_AMOUNT:
            return TransferResult.failure_result(f"Максимальная сумма перевода: {MAX_TRANSFER_AMOUNT} монет", amount)

        if sender_name.lower() == receiver_name.lower():
            return TransferResult.failure_result("Нельзя переводить деньги самому себе!", amount)

        if not self.user_exists(channel_name, receiver_name):
            return TransferResult.failure_result(f"Пользователь @{receiver_name} не найден в системе!", amount)

        db = SessionLocal()
        try:
            normalized_sender_name = sender_name.lower()
            normalized_receiver_name = receiver_name.lower()

            sender_balance = self.get_user_balance(channel_name, sender_name)
            receiver_balance = self.get_user_balance(channel_name, receiver_name)

            sender_balance = db.merge(sender_balance)
            receiver_balance = db.merge(receiver_balance)

            if sender_balance.balance < amount:
                return TransferResult.failure_result(f"Недостаточно средств! У вас {sender_balance.balance} монет, нужно {amount}", amount)

            sender_balance_before = sender_balance.balance
            receiver_balance_before = receiver_balance.balance

            sender_balance.balance -= amount
            sender_balance.total_spent += amount
            sender_balance.updated_at = datetime.utcnow()

            receiver_balance.balance += amount
            receiver_balance.total_earned += amount
            receiver_balance.updated_at = datetime.utcnow()

            self._create_transaction(db, channel_name, normalized_sender_name, TransactionType.TRANSFER_SENT, -amount, sender_balance_before, sender_balance.balance,
                                     f"Перевод {amount} монет пользователю {normalized_receiver_name}")

            self._create_transaction(db, channel_name, normalized_receiver_name, TransactionType.TRANSFER_RECEIVED, amount, receiver_balance_before, receiver_balance.balance,
                                     f"Получен перевод {amount} монет от {normalized_sender_name}")

            db.commit()

            logger.info(
                f"Перевод выполнен: {normalized_sender_name} -> {normalized_receiver_name}, сумма: {amount}, баланс отправителя: {sender_balance.balance}, баланс получателя: {receiver_balance.balance}")

            return TransferResult.success_result(amount=amount, sender_balance=sender_balance.balance, receiver_balance=receiver_balance.balance,
                                                 sender_name=sender_name, receiver_name=receiver_name)

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при переводе денег от {sender_name} к {receiver_name}: {e}")
            return TransferResult.failure_result("Произошла ошибка при выполнении перевода", amount)
        finally:
            db.close()

    def can_claim_daily_bonus(self, channel_name: str, user_name: str) -> bool:
        db = SessionLocal()
        try:
            active_stream = self.stream_service.get_active_stream(channel_name)
            if not active_stream:
                return False

            normalized_user_name = user_name.lower()

            user_balance = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .first()
            )

            if not user_balance:
                return True

            if user_balance.last_bonus_stream_id is None:
                return True

            return user_balance.last_bonus_stream_id != active_stream.id
        finally:
            db.close()

    def claim_daily_bonus(self, channel_name: str, user_name: str, user_equipment: list[UserEquipmentItem] = None) -> DailyBonusResult:
        normalized_user_name = user_name.lower()

        db = SessionLocal()
        try:
            active_stream = self.stream_service.get_active_stream(channel_name)
            if not active_stream:
                return DailyBonusResult(success=False, failure_reason="no_stream")

            user_balance = self.get_user_balance(channel_name, user_name)
            user_balance = db.merge(user_balance)

            if user_balance.last_bonus_stream_id == active_stream.id:
                return DailyBonusResult(success=False, failure_reason="already_claimed")

            equipment = user_equipment or []
            total_multiplier = 1.0
            bonus_messages = []
            special_items = []

            for item in equipment:
                for effect in item.shop_item.effects:
                    if isinstance(effect, DailyBonusMultiplierEffect):
                        special_items.append(item.shop_item.name)
                        total_multiplier *= effect.multiplier

                        if item.item_type == ShopItemType.FREEZER_DUMPLINGS:
                            bonus_messages.append("🥟 Нашелся счастливый пельмень, который увеличил бонус!")
                        elif item.item_type == ShopItemType.OCTOPUSES:
                            bonus_messages.append("🐙 Осьминоги принесли сокровища со дна и увеличили бонус!")
                        elif item.item_type == ShopItemType.MAEL_EXPEDITION:
                            bonus_messages.append("🎨 Маэль перерисовала твою судьбу и увеличила бонус! Фоном играет \"Алиииинаааа аииииии\"...")
                        elif item.item_type == ShopItemType.COMMUNIST_PARTY:
                            bonus_messages.append("☭ Партия коммунистов обеспечила тебе увеличенный бонус! Единство силу даёт, товарищ!")

            bonus_amount = int(self.DAILY_BONUS * total_multiplier)

            bonus_message = ""
            if bonus_messages:
                if len(bonus_messages) > 1:
                    bonus_message = f"🔥 СТАК БОНУСОВ! {' + '.join(bonus_messages)}"
                else:
                    bonus_message = bonus_messages[0]

            balance_before = user_balance.balance
            user_balance.balance += bonus_amount
            user_balance.total_earned += bonus_amount
            user_balance.last_daily_claim = datetime.utcnow()
            user_balance.last_bonus_stream_id = active_stream.id
            user_balance.updated_at = datetime.utcnow()

            transaction_description = "Бонус" + (f" (усилен {special_items})" if special_items else "")
            self._create_transaction(db, channel_name, normalized_user_name, TransactionType.DAILY_BONUS, bonus_amount, balance_before, user_balance.balance,
                                     transaction_description)

            db.commit()
            logger.info(f"Пользователь {normalized_user_name} получил бонус {bonus_amount}")

            db.refresh(user_balance)
            return DailyBonusResult(success=True, user_balance=user_balance, bonus_amount=bonus_amount, bonus_message=bonus_message)
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при получении стримового бонуса пользователем {user_name}: {e}")
            return DailyBonusResult(success=False, failure_reason="error")
        finally:
            db.close()

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

    def process_bet_result_with_amount(self, channel_name: str, user_name: str, result_type: str, slot_result: str, bet_amount: int,
                                       equipment: list[UserEquipmentItem]) -> BetResult:
        if bet_amount < self.MIN_BET_AMOUNT:
            return BetResult.failure_result(f"Минимальная сумма ставки: {self.MIN_BET_AMOUNT} монет. Указано: {bet_amount} монет.", bet_amount)

        if bet_amount > self.MAX_BET_AMOUNT:
            return BetResult.failure_result(f"Максимальная сумма ставки: {self.MAX_BET_AMOUNT} монет. Указано: {bet_amount} монет.", bet_amount)

        rarity_level = self._determine_correct_rarity(slot_result, result_type)

        user_balance = self.subtract_balance(channel_name, user_name, bet_amount, TransactionType.BET_LOSS, f"Ставка в слот-машине: {slot_result}")

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

            user_balance = self.add_balance(channel_name, user_name, payout, transaction_type, description)

        return BetResult.success_result(bet_cost=bet_amount, payout=payout, balance=user_balance.balance, result_type=result_type, rarity_level=rarity_level,
                                        timeout_seconds=timeout_seconds)

    def can_join_battle(self, channel_name: str, user_name: str) -> bool:
        user_balance = self.get_user_balance(channel_name, user_name)
        return user_balance.balance >= self.BATTLE_ENTRY_FEE

    def process_battle_entry(self, channel_name: str, user_name: str) -> Optional[UserBalance]:
        return self.subtract_balance(channel_name, user_name, self.BATTLE_ENTRY_FEE, TransactionType.BATTLE_PARTICIPATION, "Участие в битве")

    def process_battle_win(self, channel_name: str, winner: str, loser: str) -> UserBalance:
        return self.add_balance(channel_name, winner, self.BATTLE_WINNER_PRIZE, TransactionType.BATTLE_WIN, f"Победа в битве против {loser}")

    def get_user_stats(self, channel_name: str, user_name: str) -> UserStats:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            user_balance = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .first()
            )

            if not user_balance:
                user_balance = UserBalance(channel_name=channel_name, user_name=normalized_user_name, balance=self.STARTING_BALANCE)
                db.add(user_balance)
                self._create_transaction(db, channel_name, normalized_user_name, TransactionType.ADMIN_ADJUST, self.STARTING_BALANCE, 0, self.STARTING_BALANCE,
                                         "Создание нового аккаунта")
                db.commit()
                logger.info(f"Создан новый пользователь {normalized_user_name} с балансом {self.STARTING_BALANCE}")

            transactions = (
                db.query(TransactionHistory)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .all()
            )

            transaction_counts = {}
            for transaction_type in TransactionType:
                count = sum(1 for t in transactions if t.transaction_type == transaction_type)
                if count > 0:
                    transaction_counts[transaction_type.value] = count

            return UserStats(
                balance=user_balance.balance,
                total_earned=user_balance.total_earned,
                total_spent=user_balance.total_spent,
                net_profit=user_balance.total_earned - user_balance.total_spent,
                last_daily_claim=user_balance.last_daily_claim,
                can_claim_daily=self.can_claim_daily_bonus(channel_name, user_name),
                created_at=user_balance.created_at,
                transaction_counts=transaction_counts
            )
        finally:
            db.close()

    def get_top_users(self, channel_name: str, limit: int = 10) -> list:
        db = SessionLocal()
        try:
            top_users = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, is_active=True)
                .order_by(UserBalance.balance.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "user_name": user.user_name,
                    "balance": user.balance,
                    "total_earned": user.total_earned,
                    "total_spent": user.total_spent
                }
                for user in top_users
            ]
        finally:
            db.close()

    def get_bottom_users(self, channel_name: str, limit: int = 10) -> list:
        db = SessionLocal()
        try:
            bottom_users = (
                db.query(UserBalance)
                .filter_by(channel_name=channel_name, is_active=True)
                .order_by(UserBalance.balance.asc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "user_name": user.user_name,
                    "balance": user.balance,
                    "total_earned": user.total_earned,
                    "total_spent": user.total_spent
                }
                for user in bottom_users
            ]
        finally:
            db.close()

    def _create_transaction(self, db: Session, channel_name: str, user_name: str, transaction_type: TransactionType, amount: int, balance_before: int, balance_after: int,
                            description: str = None):
        transaction = TransactionHistory(
            channel_name=channel_name,
            user_name=user_name,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
        )
        db.add(transaction)

    def purchase_item(self, channel_name: str, user_name: str, item_name: str) -> dict:
        try:
            item_type = ShopItems.find_item_by_name(item_name)
            item = ShopItems.get_item(item_type)
        except ValueError as e:
            return {
                "success": False,
                "message": str(e)
            }

        db = SessionLocal()
        try:
            user_balance = self.get_user_balance(channel_name, user_name)
            user_balance = db.merge(user_balance)

            if user_balance.balance < item.price:
                return {
                    "success": False,
                    "message": f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
                }

            normalized_user_name = user_name.lower()

            existing_item = (
                db.query(UserEquipment)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name, item_type=item_type)
                .filter(UserEquipment.expires_at > datetime.utcnow())
                .first()
            )

            if existing_item:
                return {
                    "success": False,
                    "message": f"У вас уже есть '{item.name}' до {existing_item.expires_at.strftime('%d.%m.%Y')}"
                }

            balance_before = user_balance.balance
            user_balance.balance -= item.price
            user_balance.total_spent += item.price
            user_balance.updated_at = datetime.utcnow()

            self._create_transaction(db, channel_name, normalized_user_name, TransactionType.SHOP_PURCHASE, -item.price, balance_before, user_balance.balance,
                                     f"Покупка '{item.name}'")

            equipment = UserEquipment(
                channel_name=channel_name,
                user_name=normalized_user_name,
                item_type=item_type,
                expires_at=UserEquipment.get_expiry_date()
            )
            db.add(equipment)

            db.commit()

            logger.info(f"Пользователь {normalized_user_name} купил '{item.name}' за {item.price} монет")

            return {
                "success": True,
                "item": item,
                "new_balance": user_balance.balance,
                "expires_at": equipment.expires_at
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при покупке предмета пользователем {user_name}: {e}")
            return {
                "success": False,
                "message": "Произошла ошибка при покупке предмета"
            }
        finally:
            db.close()

    def cleanup_expired_equipment(self, channel_name: str) -> int:
        db = SessionLocal()
        try:
            expired_count = (
                db.query(UserEquipment)
                .filter_by(channel_name=channel_name)
                .filter(UserEquipment.expires_at <= datetime.utcnow())
                .delete()
            )

            db.commit()
            logger.info(f"Удалено {expired_count} просроченных предметов экипировки")
            return expired_count

        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при очистке просроченной экипировки: {e}")
            return 0
        finally:
            db.close()

    def calculate_timeout_with_equipment(self, user_name: str, base_timeout_seconds: int, equipment: list[UserEquipmentItem]) -> tuple[int, str]:
        if base_timeout_seconds <= 0:
            return 0, ""

        if not equipment:
            return base_timeout_seconds, ""

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutProtectionEffect):
                    logger.info(f"⚡ ЗАЩИТА ОТ ТАЙМАУТА: {user_name} спасен предметом {item.shop_item.name} (базовый таймаут: {base_timeout_seconds}с)")

                    if item.item_type == ShopItemType.MAEL_EXPEDITION:
                        return 0, "⚔️ Маэль перерисовала судьбу и полностью спасла от таймаута! Фоном играет \"Алиииинаааа аииииии\"..."
                    elif item.item_type == ShopItemType.COMMUNIST_PARTY:
                        return 0, "☭ Партия коммунистов защитила товарища! Единство спасло от таймаута!"
                    elif item.item_type == ShopItemType.GAMBLER_AMULET:
                        return 0, "🎰 Амулет лудомана защитил от таймаута!"
                    else:
                        return 0, f"{item.shop_item.emoji} {item.shop_item.name} спас от таймаута!"

        reduction_items = []
        cumulative_reduction = 1.0
        timeout_messages = []

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutReductionEffect):
                    reduction_items.append(item)
                    cumulative_reduction *= effect.reduction_factor

                    if item.item_type == ShopItemType.CHAIR:
                        timeout_messages.append("🪑 Стул обеспечил надёжную опору и снизил таймаут!")
                    elif item.item_type == ShopItemType.BONFIRE:
                        timeout_messages.append("🔥 Костёр согрел душу и стал чекпоинтом, снизив таймаут!")
                    else:
                        timeout_messages.append(f"{item.shop_item.emoji} {item.shop_item.name} снизил таймаут!")

                    logger.info(f"⚡ СНИЖЕНИЕ ТАЙМАУТА: {user_name} применен эффект от {item.shop_item.name} (множитель: {effect.reduction_factor})")

        if reduction_items:
            reduced_timeout = int(base_timeout_seconds * cumulative_reduction)

            if len(timeout_messages) == 1:
                message = timeout_messages[0]
            else:
                message = f"🔥 СТАК ЗАЩИТЫ! {' + '.join(timeout_messages)}"

            logger.info(f"⚡ ИТОГОВОЕ СНИЖЕНИЕ ТАЙМАУТА: {user_name} (было: {base_timeout_seconds}с, стало: {reduced_timeout}с, общий множитель: {cumulative_reduction:.2f})")
            return reduced_timeout, message

        return base_timeout_seconds, ""

    def calculate_roll_cooldown_seconds(self, default_cooldown_seconds: int, equipment: list[UserEquipmentItem]) -> int:
        min_cooldown = default_cooldown_seconds
        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, RollCooldownOverrideEffect):
                    min_cooldown = min(min_cooldown, effect.cooldown_seconds)
        return min_cooldown
