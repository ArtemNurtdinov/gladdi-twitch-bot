import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from features.economy.db.transaction_history import TransactionType
from features.economy.domain.models import UserBalanceInfo, TransactionData, BalanceBrief
from features.economy.domain.repo import EconomyRepository
from features.economy.model.daily_bonus import DailyBonusResult
from features.equipment.model.user_equipment_item import UserEquipmentItem
from features.economy.model.transfer_result import TransferResult
from features.economy.model.shop_items import ShopItemType, DailyBonusMultiplierEffect

logger = logging.getLogger(__name__)


class EconomyService:
    STARTING_BALANCE = 1000
    DAILY_BONUS = 200

    MIN_TRANSFER_AMOUNT = 100
    MAX_TRANSFER_AMOUNT = 50000

    ACTIVITY_MESSAGES_REQUIRED = 1
    ACTIVITY_REWARD = 10
    ACTIVITY_COOLDOWN_MINUTES = 10

    BATTLE_ENTRY_FEE = 500
    BATTLE_WINNER_PRIZE = 1000

    def __init__(self, repo: EconomyRepository[Session]):
        self._repo = repo

    def _should_grant_activity_reward(self, user_balance: UserBalanceInfo) -> bool:
        if user_balance.last_activity_reward is not None:
            time_since_last = datetime.utcnow() - user_balance.last_activity_reward
            if time_since_last < timedelta(minutes=self.ACTIVITY_COOLDOWN_MINUTES):
                return False

        return True

    def process_user_message_activity(self, db: Session, channel_name: str, user_name: str):
        user_balance = self.get_user_balance(db, channel_name, user_name)

        user_balance.message_count += 1
        user_balance.updated_at = datetime.utcnow()

        if not self._should_grant_activity_reward(user_balance):
            self._repo.save_balance(db, user_balance)
            return None

        user_balance.last_activity_reward = datetime.utcnow()

        balance_before = user_balance.balance
        user_balance.balance += self.ACTIVITY_REWARD
        user_balance.total_earned += self.ACTIVITY_REWARD
        user_balance.updated_at = datetime.utcnow()

        self._repo.save_balance(db, user_balance)
        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=user_name,
                transaction_type=TransactionType.MESSAGE_REWARD,
                amount=self.ACTIVITY_REWARD,
                balance_before=balance_before,
                balance_after=user_balance.balance,
                description="Награда за активность в чате",
                created_at=datetime.utcnow(),
            ),
        )

    def get_user_balance(self, db: Session, channel_name: str, user_name: str) -> UserBalanceInfo:
        normalized_user_name = user_name.lower()
        user_balance = self._repo.get_balance(db, channel_name, normalized_user_name)

        if not user_balance:
            user_balance = self._repo.create_balance(db, channel_name, normalized_user_name, self.STARTING_BALANCE)
            self._repo.add_transaction(
                db,
                TransactionData(
                    channel_name=channel_name,
                    user_name=normalized_user_name,
                    transaction_type=TransactionType.ADMIN_ADJUST,
                    amount=self.STARTING_BALANCE,
                    balance_before=0,
                    balance_after=self.STARTING_BALANCE,
                    description="Создание нового аккаунта",
                    created_at=datetime.utcnow(),
                ),
            )

        return user_balance

    def add_balance(self, db: Session, channel_name: str, user_name: str, amount: int, transaction_type: TransactionType, description: str = None) -> UserBalanceInfo:
        normalized_user_name = user_name.lower()

        user_balance = self.get_user_balance(db, channel_name, normalized_user_name)

        balance_before = user_balance.balance or 0
        user_balance.balance = (user_balance.balance or 0) + amount
        user_balance.total_earned = (user_balance.total_earned or 0) + max(0, amount)
        user_balance.updated_at = datetime.utcnow()

        saved = self._repo.save_balance(db, user_balance)
        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=normalized_user_name,
                transaction_type=transaction_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=saved.balance,
                description=description,
                created_at=datetime.utcnow(),
            ),
        )
        return saved

    def subtract_balance(self, db: Session, channel_name: str, user_name: str, amount: int, transaction_type: TransactionType, description: str = None) -> Optional[UserBalanceInfo]:
        normalized_user_name = user_name.lower()

        user_balance = self.get_user_balance(db, channel_name, normalized_user_name)

        current_balance = user_balance.balance or 0
        if current_balance < amount:
            logger.warning(f"Недостаточно средств у {normalized_user_name}: {current_balance} < {amount}")
            return None

        balance_before = current_balance
        user_balance.balance = current_balance - amount
        user_balance.total_spent = (user_balance.total_spent or 0) + amount
        user_balance.updated_at = datetime.utcnow()

        saved = self._repo.save_balance(db, user_balance)
        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=normalized_user_name,
                transaction_type=transaction_type,
                amount=-amount,
                balance_before=balance_before,
                balance_after=saved.balance,
                description=description,
                created_at=datetime.utcnow(),
            ),
        )

        logger.info(f"У пользователя {normalized_user_name} списано {amount} монет. Новый баланс: {saved.balance}")

        return saved

    def transfer_money(self, db: Session, channel_name: str, sender_name: str, receiver_name: str, amount: int) -> TransferResult:
        if amount < self.MIN_TRANSFER_AMOUNT:
            return TransferResult.failure_result(f"Минимальная сумма перевода: {self.MIN_TRANSFER_AMOUNT} монет")

        if amount > self.MAX_TRANSFER_AMOUNT:
            return TransferResult.failure_result(f"Максимальная сумма перевода: {self.MAX_TRANSFER_AMOUNT} монет")

        if sender_name == receiver_name:
            return TransferResult.failure_result("Нельзя переводить деньги самому себе!")

        receiver_balance = self._repo.get_balance(db, channel_name, receiver_name)

        if receiver_balance is None:
            return TransferResult.failure_result(f"Пользователь @{receiver_name} не найден в системе!")

        sender_balance = self.get_user_balance(db, channel_name, sender_name)
        receiver_balance = self.get_user_balance(db, channel_name, receiver_name)

        if sender_balance.balance < amount:
            return TransferResult.failure_result(f"Недостаточно средств! У вас {sender_balance.balance} монет, нужно {amount}")

        sender_balance_before = sender_balance.balance
        receiver_balance_before = receiver_balance.balance

        sender_balance.balance -= amount
        sender_balance.total_spent += amount
        sender_balance.updated_at = datetime.utcnow()

        receiver_balance.balance += amount
        receiver_balance.total_earned += amount
        receiver_balance.updated_at = datetime.utcnow()

        sender_saved = self._repo.save_balance(db, sender_balance)
        receiver_saved = self._repo.save_balance(db, receiver_balance)

        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=sender_name,
                transaction_type=TransactionType.TRANSFER_SENT,
                amount=-amount,
                balance_before=sender_balance_before,
                balance_after=sender_saved.balance,
                description=f"Перевод {amount} монет пользователю {receiver_name}",
                created_at=datetime.utcnow(),
            ),
        )

        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=receiver_name,
                transaction_type=TransactionType.TRANSFER_RECEIVED,
                amount=amount,
                balance_before=receiver_balance_before,
                balance_after=receiver_saved.balance,
                description=f"Получен перевод {amount} монет от {sender_name}",
                created_at=datetime.utcnow(),
            ),
        )
        return TransferResult.success_result()

    def claim_daily_bonus(self, db: Session, active_stream_id: int, channel_name: str, user_name: str, user_equipment: list[UserEquipmentItem] = None) -> DailyBonusResult:
        user_balance = self.get_user_balance(db, channel_name, user_name)

        if user_balance.last_bonus_stream_id == active_stream_id:
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
                        bonus_messages.append("Нашелся счастливый пельмень, который увеличил бонус!")
                    elif item.item_type == ShopItemType.OCTOPUSES:
                        bonus_messages.append("Осьминоги принесли сокровища со дна и увеличили бонус!")
                    elif item.item_type == ShopItemType.MAEL_EXPEDITION:
                        bonus_messages.append("Маэль перерисовала твою судьбу и увеличила бонус! Фоном играет \"Алиииинаааа аииииии\"...")
                    elif item.item_type == ShopItemType.COMMUNIST_PARTY:
                        bonus_messages.append("Партия коммунистов обеспечила тебе увеличенный бонус! Единство силу даёт, товарищ!")

        bonus_amount = int(self.DAILY_BONUS * total_multiplier)

        bonus_message = ""
        if bonus_messages:
            if len(bonus_messages) > 1:
                bonus_message = f"СТАК БОНУСОВ! {' + '.join(bonus_messages)}"
            else:
                bonus_message = bonus_messages[0]

        balance_before = user_balance.balance
        user_balance.balance += bonus_amount
        user_balance.total_earned += bonus_amount
        user_balance.last_daily_claim = datetime.utcnow()
        user_balance.last_bonus_stream_id = active_stream_id
        user_balance.updated_at = datetime.utcnow()

        transaction_description = "Бонус" + (f" (усилен {special_items})" if special_items else "")

        saved = self._repo.save_balance(db, user_balance)

        self._repo.add_transaction(
            db,
            TransactionData(
                channel_name=channel_name,
                user_name=user_name,
                transaction_type=TransactionType.DAILY_BONUS,
                amount=bonus_amount,
                balance_before=balance_before,
                balance_after=saved.balance,
                description=transaction_description,
                created_at=datetime.utcnow(),
            ),
        )

        logger.info(f"Пользователь {user_name} получил бонус {bonus_amount}")

        return DailyBonusResult(success=True, user_balance=saved, bonus_amount=bonus_amount, bonus_message=bonus_message)

    def get_top_users(self, db: Session, channel_name: str, limit: int) -> list[BalanceBrief]:
        return self._repo.get_top_users(db, channel_name, limit)

    def get_bottom_users(self, db: Session, channel_name: str, limit: int) -> list[BalanceBrief]:
        return self._repo.get_bottom_users(db, channel_name, limit)
