import random
from datetime import datetime
from typing import Any, Awaitable, Callable

from sqlalchemy.orm import Session

from app.betting.domain.betting_service import BettingService
from app.betting.domain.models import EmojiConfig, RarityLevel
from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import (
    JackpotPayoutMultiplierEffect,
    MissPayoutMultiplierEffect,
    PartialPayoutMultiplierEffect,
    TransactionType,
)
from app.equipment.domain.equipment_service import EquipmentService
from core.db import SessionLocal, db_ro_session


class RollCommandHandler:
    DEFAULT_COOLDOWN_SECONDS = 60
    CLEANUP_THRESHOLD_SECONDS = 300

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        economy_service_factory: Callable[[Session], EconomyService],
        betting_service_factory: Callable[[Session], BettingService],
        equipment_service_factory: Callable[[Session], EquipmentService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        timeout_fn: Callable[[str, str, int, str], Awaitable[None]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self._economy_service = economy_service_factory
        self._betting_service = betting_service_factory
        self._equipment_service = equipment_service_factory
        self._chat_use_case = chat_use_case_factory
        self.roll_cooldowns: dict[str, datetime] = {}
        self.timeout_user = timeout_fn
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    def _cleanup_old_cooldowns(self):
        current_time = datetime.now()
        cleanup_threshold = self.CLEANUP_THRESHOLD_SECONDS

        old_nicknames = [
            nickname
            for nickname, last_time in self.roll_cooldowns.items()
            if (current_time - last_time).total_seconds() > cleanup_threshold
        ]

        for nickname in old_nicknames:
            del self.roll_cooldowns[nickname]

    @staticmethod
    def is_miss(result_type: str) -> bool:
        return result_type == "miss"

    @staticmethod
    def is_consolation_prize(result_type: str, payout: int) -> bool:
        return result_type == "miss" and payout > 0

    @staticmethod
    def is_jackpot(result_type: str) -> bool:
        return result_type == "jackpot"

    @staticmethod
    def is_partial_match(result_type: str) -> bool:
        return result_type == "partial"

    def get_result_emoji(self, result_type: str, payout: int) -> str:
        if self.is_consolation_prize(result_type, payout):
            return "🎁"
        if self.is_jackpot(result_type):
            return "🎰"
        if self.is_partial_match(result_type):
            return "✨"
        if self.is_miss(result_type):
            return "💥"
        return "💰"

    def get_profit_display(self, result_type: str, payout: int, profit: int) -> str:
        if self.is_consolation_prize(result_type, payout):
            net_result = profit
            if net_result > 0:
                return f"+{net_result}"
            if net_result < 0:
                return f"{net_result}"
            return "±0"
        if profit > 0:
            return f"+{profit}"
        if profit < 0:
            return f"{profit}"
        return "±0"

    async def handle(self, ctx, channel_name: str, display_name: str, amount: str | None = None):
        self._cleanup_old_cooldowns()

        user_name = display_name.lower()
        bet_amount = BettingService.BET_COST
        if amount:
            try:
                bet_amount = int(amount)
            except ValueError:
                result = (
                    f"@{display_name}, неверная сумма ставки! Используй: {self.command_prefix}{self.command_name} [сумма] "
                    f"(например: {self.command_prefix}{self.command_name} 100). "
                    f"Диапазон: {BettingService.MIN_BET_AMOUNT}-{BettingService.MAX_BET_AMOUNT} монет."
                )
                bot_nick = self.bot_nick_provider().lower()
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
                await self.post_message_fn(result, ctx)
                return

        current_time = datetime.now()
        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)
            cooldown_seconds = self._equipment_service(db).calculate_roll_cooldown_seconds(
                default_cooldown_seconds=RollCommandHandler.DEFAULT_COOLDOWN_SECONDS,
                equipment=equipment
            )

        if display_name in self.roll_cooldowns:
            time_since_last = (current_time - self.roll_cooldowns[display_name]).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{display_name}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                bot_nick = self.bot_nick_provider().lower()
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
                await self.post_message_fn(result, ctx)
                return

        self.roll_cooldowns[display_name] = current_time

        emojis = EmojiConfig.get_emojis_list()
        weights = EmojiConfig.get_weights_list()

        slot_results = random.choices(emojis, weights=weights, k=3)
        slot_result_string = EmojiConfig.format_slot_result(slot_results)

        unique_results = set(slot_results)

        if len(unique_results) == 1:
            result_type = "jackpot"
        elif len(unique_results) == 2:
            result_type = "partial"
        else:
            result_type = "miss"

        if bet_amount < BettingService.MIN_BET_AMOUNT:
            result = f"Минимальная сумма ставки: {BettingService.MIN_BET_AMOUNT} монет."
            bot_nick = self.bot_nick_provider().lower()
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if bet_amount > BettingService.MAX_BET_AMOUNT:
            result = f"Максимальная сумма ставки: {BettingService.MAX_BET_AMOUNT} монет."
            bot_nick = self.bot_nick_provider().lower()
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        with db_ro_session() as db:
            rarity_level = self._betting_service(db).determine_correct_rarity(slot_result_string, result_type)
            equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).subtract_balance(
                channel_name,
                user_name,
                bet_amount,
                TransactionType.BET_LOSS,
                f"Ставка в слот-машине: {slot_result_string}"
            )
            if not user_balance:
                result = f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет."
                bot_nick = self.bot_nick_provider().lower()
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
                await self.post_message_fn(result, ctx)
                return
            base_payout = BettingService.RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
            timeout_seconds = None
            if result_type == "jackpot":
                payout = base_payout * BettingService.JACKPOT_MULTIPLIER
            elif result_type == "partial":
                payout = base_payout * BettingService.PARTIAL_MULTIPLIER
            else:
                consolation_prize = BettingService.CONSOLATION_PRIZES.get(rarity_level, 0)
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
                transaction_type = TransactionType.BET_WIN
                description = (
                    f"Выигрыш в слот-машине: {slot_result_string}"
                    if result_type != "miss"
                    else f"Консольный приз: {slot_result_string}"
                )
                user_balance = self._economy_service(db).add_balance(
                    channel_name, user_name, payout, transaction_type, description
                )
            self._betting_service(db).save_bet(channel_name, user_name, slot_result_string, result_type, rarity_level)

        result_emoji = self.get_result_emoji(result_type, payout)

        economic_info = f" {result_emoji} Баланс: {user_balance.balance} монет"

        profit = payout - bet_amount

        profit_display = self.get_profit_display(result_type, payout, profit)

        economic_info += f" ({profit_display})"

        final_result = f"{slot_result_string} {economic_info}"

        with SessionLocal.begin() as db:
            bot_nick = self.bot_nick_provider().lower()
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, final_result, datetime.utcnow())

        await self.post_message_fn(final_result, ctx)

        if timeout_seconds is not None and timeout_seconds > 0:
            base_timeout_duration = timeout_seconds if timeout_seconds else 0

            with db_ro_session() as db:
                equipment = self._equipment_service(db).get_user_equipment(channel_name, user_name)
                final_timeout, protection_message = self._equipment_service(db).calculate_timeout_with_equipment(
                    base_timeout_duration,
                    equipment
                )

            if final_timeout == 0:
                if self.is_consolation_prize(result_type, payout):
                    no_timeout_message = f"🎁 @{display_name}, {protection_message} Консольный приз: {payout} монет"
                else:
                    no_timeout_message = f"🛡️ @{display_name}, {protection_message}"

                with SessionLocal.begin() as db:
                    bot_nick = self.bot_nick_provider().lower()
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick, no_timeout_message, datetime.utcnow())

                await self.post_message_fn(no_timeout_message, ctx)
            else:
                if self.is_consolation_prize(result_type, payout):
                    reason = f"Промах с редким эмодзи! Консольный приз: {payout} монет. Таймаут: {final_timeout} сек ⏰"
                else:
                    reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                await self.post_message_fn(reason, ctx)

                await self.timeout_user(channel_name, display_name, final_timeout, reason)
        elif self.is_miss(result_type):
            if self.is_consolation_prize(result_type, payout):
                no_timeout_message = f"🎁 @{display_name}, повезло! Редкий эмодзи спас от таймаута! Консольный приз: {payout} монет"
            else:
                no_timeout_message = f"✨ @{display_name}, редкий эмодзи спас от таймаута!"

            await self.post_message_fn(no_timeout_message, ctx)
