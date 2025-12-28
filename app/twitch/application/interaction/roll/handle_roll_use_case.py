import random
from datetime import datetime
from typing import Callable, ContextManager, List, Optional

from sqlalchemy.orm import Session

from app.betting.application.betting_service_provider import BettingServiceProvider
from app.twitch.application.interaction.roll.dto import RollDTO, RollUseCaseResult, RollTimeoutAction
from app.betting.application.betting_service import BettingService
from app.betting.domain.models import EmojiConfig, RarityLevel
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.economy.application.economy_service_provider import EconomyServiceProvider
from app.economy.domain.models import JackpotPayoutMultiplierEffect, MissPayoutMultiplierEffect, PartialPayoutMultiplierEffect, \
    TransactionType
from app.equipment.application.equipment_service_provider import EquipmentServiceProvider


class HandleRollUseCase:
    DEFAULT_COOLDOWN_SECONDS = 60

    def __init__(
        self,
        economy_service_provider: EconomyServiceProvider,
        betting_service_provider: BettingServiceProvider,
        equipment_service_provider: EquipmentServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider
    ):
        self._economy_service_provider = economy_service_provider
        self._betting_service_provider = betting_service_provider
        self._equipment_service_provider = equipment_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: RollDTO,
    ) -> RollUseCaseResult:
        messages: List[str] = []
        timeout_action: Optional[RollTimeoutAction] = None
        current_time = datetime.now()

        with db_readonly_session_provider() as db:
            equipment = self._equipment_service_provider.get(db).get_user_equipment(dto.channel_name, dto.user_name)
            cooldown_seconds = self._equipment_service_provider.get(db).calculate_roll_cooldown_seconds(
                default_cooldown_seconds=HandleRollUseCase.DEFAULT_COOLDOWN_SECONDS,
                equipment=equipment,
            )

        if dto.last_roll_time:
            time_since_last = (current_time - dto.last_roll_time).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{dto.display_name}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                with db_session_provider() as db:
                    self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=dto.last_roll_time)

        bet_amount = BettingService.BET_COST
        if dto.amount_input:
            try:
                bet_amount = int(dto.amount_input)
            except ValueError:
                result = (
                    f"@{dto.display_name}, неверная сумма ставки! Используй: "
                    f"{dto.command_prefix}{dto.command_name} [сумма] "
                    f"(например: {dto.command_prefix}{dto.command_name} 100). "
                    f"Диапазон: {BettingService.MIN_BET_AMOUNT}-{BettingService.MAX_BET_AMOUNT} монет."
                )
                with db_session_provider() as db:
                    self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=dto.last_roll_time)

        new_last_roll_time = current_time

        if bet_amount < BettingService.MIN_BET_AMOUNT:
            result = f"Минимальная сумма ставки: {BettingService.MIN_BET_AMOUNT} монет."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            messages.append(result)
            return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=new_last_roll_time)

        if bet_amount > BettingService.MAX_BET_AMOUNT:
            result = f"Максимальная сумма ставки: {BettingService.MAX_BET_AMOUNT} монет."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            messages.append(result)
            return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=new_last_roll_time)

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

        with db_readonly_session_provider() as db:
            rarity_level = self._betting_service_provider.get(db).determine_correct_rarity(slot_result_string, result_type)
            equipment = self._equipment_service_provider.get(db).get_user_equipment(dto.channel_name, dto.user_name)

        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).subtract_balance(
                dto.channel_name,
                dto.user_name,
                bet_amount,
                TransactionType.BET_LOSS,
                f"Ставка в слот-машине: {slot_result_string}",
            )
            if not user_balance:
                result = f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет."
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=new_last_roll_time)

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
                user_balance = self._economy_service_provider.get(db).add_balance(
                    dto.channel_name, dto.user_name, payout, transaction_type, description
                )
            self._betting_service_provider.get(db).save_bet(dto.channel_name, dto.user_name, slot_result_string, result_type, rarity_level)

        result_emoji = self._get_result_emoji(result_type, payout)
        profit = payout - bet_amount
        profit_display = self._get_profit_display(result_type, payout, profit)
        final_result = f"{slot_result_string} {result_emoji} Баланс: {user_balance.balance} монет ({profit_display})"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, final_result, dto.occurred_at)
        messages.append(final_result)

        if timeout_seconds is not None and timeout_seconds > 0:
            base_timeout_duration = timeout_seconds if timeout_seconds else 0

            with db_readonly_session_provider() as db:
                equipment = self._equipment_service_provider.get(db).get_user_equipment(dto.channel_name, dto.user_name)
                final_timeout, protection_message = self._equipment_service_provider.get(db).calculate_timeout_with_equipment(
                    base_timeout_duration,
                    equipment,
                )

            if final_timeout == 0:
                if self._is_consolation_prize(result_type, payout):
                    no_timeout_message = (
                        f"🎁 @{dto.display_name}, {protection_message} Консольный приз: {payout} монет"
                    )
                else:
                    no_timeout_message = f"🛡️ @{dto.display_name}, {protection_message}"

                with db_session_provider() as db:
                    self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, dto.bot_nick, no_timeout_message,
                                                                           dto.occurred_at)
                messages.append(no_timeout_message)
            else:
                if self._is_consolation_prize(result_type, payout):
                    reason = (
                        f"Промах с редким эмодзи! Консольный приз: {payout} монет. Таймаут: {final_timeout} сек ⏰"
                    )
                else:
                    reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                timeout_action = RollTimeoutAction(
                    user_name=dto.display_name,
                    duration_seconds=final_timeout,
                    reason=reason,
                )
        elif self._is_miss(result_type):
            if self._is_consolation_prize(result_type, payout):
                no_timeout_message = (
                    f"🎁 @{dto.display_name}, повезло! Редкий эмодзи спас от таймаута! Консольный приз: {payout} монет"
                )
            else:
                no_timeout_message = f"✨ @{dto.display_name}, редкий эмодзи спас от таймаута!"

            messages.append(no_timeout_message)

        return RollUseCaseResult(messages=messages, timeout_action=timeout_action, new_last_roll_time=new_last_roll_time)

    @staticmethod
    def _is_miss(result_type: str) -> bool:
        return result_type == "miss"

    @staticmethod
    def _is_consolation_prize(result_type: str, payout: int) -> bool:
        return result_type == "miss" and payout > 0

    @staticmethod
    def _is_jackpot(result_type: str) -> bool:
        return result_type == "jackpot"

    @staticmethod
    def _is_partial_match(result_type: str) -> bool:
        return result_type == "partial"

    def _get_result_emoji(self, result_type: str, payout: int) -> str:
        if self._is_consolation_prize(result_type, payout):
            return "🎁"
        if self._is_jackpot(result_type):
            return "🎰"
        if self._is_partial_match(result_type):
            return "✨"
        if self._is_miss(result_type):
            return "💥"
        return "💰"

    def _get_profit_display(self, result_type: str, payout: int, profit: int) -> str:
        if self._is_consolation_prize(result_type, payout):
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
