import random
from datetime import datetime

from app.betting.application.betting_service import BettingService
from app.betting.domain.model.rarity import RarityLevel
from app.betting.domain.models import EmojiConfig
from app.commands.roll.application.model import RollDTO, RollTimeoutAction, RollUseCaseResult
from app.commands.roll.application.roll_uow import RollUnitOfWorkFactory
from app.economy.domain.models import TransactionType
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.domain.models import UserEquipmentItem
from app.shop.domain.models import (
    MaxBetIncreaseEffect,
)
from core.provider import SingletonProvider


def _get_max_bet_amount(equipment: list[UserEquipmentItem]) -> int:
    result = BettingService.MAX_BET_AMOUNT
    for item in equipment:
        for effect in item.shop_item.effects:
            if isinstance(effect, MaxBetIncreaseEffect) and effect.max_bet_amount > result:
                result = effect.max_bet_amount
    return result


class HandleRollUseCase:
    DEFAULT_COOLDOWN_SECONDS = 60

    def __init__(
        self,
        unit_of_work_factory: RollUnitOfWorkFactory,
        roll_cooldown_use_case_provider: SingletonProvider[RollCooldownUseCase],
        calculate_timeout_use_case_provider: SingletonProvider[CalculateTimeoutUseCase],
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._roll_cooldown_use_case_provider = roll_cooldown_use_case_provider
        self._calculate_timeout_use_case_provider = calculate_timeout_use_case_provider

    async def handle(
        self,
        command_roll: RollDTO,
    ) -> RollUseCaseResult:
        messages: list[str] = []
        timeout_action: RollTimeoutAction | None = None
        current_time = datetime.now()

        user_message = command_roll.command_prefix + command_roll.command_name
        if command_roll.amount_input:
            user_message += command_roll.amount_input

        with self._unit_of_work_factory.create(read_only=True) as uow:
            equipment = uow.get_user_equipment_use_case.get_user_equipment(
                channel_name=command_roll.channel_name, user_name=command_roll.user_name
            )
            cooldown_seconds = self._roll_cooldown_use_case_provider.get().calc_seconds(
                default_cooldown_seconds=HandleRollUseCase.DEFAULT_COOLDOWN_SECONDS, equipment=equipment
            )

        max_bet_amount = _get_max_bet_amount(equipment)

        if command_roll.last_roll_time:
            time_since_last = (current_time - command_roll.last_roll_time).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{command_roll.display_name}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                with self._unit_of_work_factory.create() as uow:
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.user_name,
                        content=user_message,
                        current_time=command_roll.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.bot_nick,
                        content=result,
                        current_time=command_roll.occurred_at,
                    )
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=command_roll.last_roll_time)

        bet_amount = BettingService.BET_COST
        if command_roll.amount_input:
            try:
                bet_amount = int(command_roll.amount_input)
            except ValueError:
                result = (
                    f"@{command_roll.display_name}, неверная сумма ставки! Используй: "
                    f"{command_roll.command_prefix}{command_roll.command_name} [сумма] "
                    f"(например: {command_roll.command_prefix}{command_roll.command_name} 100). "
                    f"Диапазон: {BettingService.MIN_BET_AMOUNT}-{max_bet_amount} монет."
                )
                with self._unit_of_work_factory.create() as uow:
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.user_name,
                        content=user_message,
                        current_time=command_roll.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.bot_nick,
                        content=result,
                        current_time=command_roll.occurred_at,
                    )
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=command_roll.last_roll_time)

        new_last_roll_time = current_time

        if bet_amount < BettingService.MIN_BET_AMOUNT:
            result = f"Минимальная сумма ставки: {BettingService.MIN_BET_AMOUNT} монет."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.user_name,
                    content=user_message,
                    current_time=command_roll.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.bot_nick,
                    content=result,
                    current_time=command_roll.occurred_at,
                )
            messages.append(result)
            return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=new_last_roll_time)

        if bet_amount > max_bet_amount:
            result = f"Максимальная сумма ставки: {max_bet_amount} монет."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.user_name,
                    content=user_message,
                    current_time=command_roll.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.bot_nick,
                    content=result,
                    current_time=command_roll.occurred_at,
                )
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

        with self._unit_of_work_factory.create(read_only=True) as uow:
            rarity_level = uow.betting_service.determine_correct_rarity(slot_result=slot_result_string, result_type=result_type)

        with self._unit_of_work_factory.create() as uow:
            user_balance = uow.economy_policy.subtract_balance(
                channel_name=command_roll.channel_name,
                user_name=command_roll.user_name,
                amount=bet_amount,
                transaction_type=TransactionType.BET_LOSS,
                description=f"Ставка в слот-машине: {slot_result_string}",
            )
            if not user_balance:
                result = f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет."
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.user_name,
                    content=user_message,
                    current_time=command_roll.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.bot_nick,
                    content=result,
                    current_time=command_roll.occurred_at,
                )
                messages.append(result)
                return RollUseCaseResult(messages=messages, timeout_action=None, new_last_roll_time=new_last_roll_time)

            base_payout = BettingService.RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
            timeout_seconds = None
            if result_type == "jackpot":
                payout = base_payout * BettingService.JACKPOT_MULTIPLIER
            elif result_type == "partial":
                payout = base_payout * BettingService.PARTIAL_MULTIPLIER
            else:
                payout = 0
                if rarity_level in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                    timeout_seconds = 0
                elif rarity_level == RarityLevel.EPIC:
                    timeout_seconds = 60
                elif rarity_level == RarityLevel.RARE:
                    timeout_seconds = 120
                else:
                    timeout_seconds = 180

            payout = int(payout) if payout > 0 else 0

            if payout > 0:
                transaction_type = TransactionType.BET_WIN
                description = f"Выигрыш в слот-машине: {slot_result_string}"
                user_balance = uow.economy_policy.add_balance(
                    channel_name=command_roll.channel_name,
                    user_name=command_roll.user_name,
                    amount=payout,
                    transaction_type=transaction_type,
                    description=description,
                )
            uow.betting_service.save_bet(
                channel_name=command_roll.channel_name,
                user_name=command_roll.user_name,
                slot_result=slot_result_string,
                result_type=result_type,
                rarity_level=rarity_level,
            )

        result_emoji = self._get_result_emoji(result_type)
        profit = payout - bet_amount
        profit_display = self._get_profit_display(profit)
        final_result = f"{slot_result_string} {result_emoji} Баланс: {user_balance.balance} монет ({profit_display})"

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_roll.channel_name,
                user_name=command_roll.user_name,
                content=user_message,
                current_time=command_roll.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_roll.channel_name,
                user_name=command_roll.bot_nick,
                content=final_result,
                current_time=command_roll.occurred_at,
            )
        messages.append(final_result)

        if timeout_seconds is not None and timeout_seconds > 0:
            base_timeout_duration = timeout_seconds if timeout_seconds else 0

            final_timeout, protection_message = self._calculate_timeout_use_case_provider.get().calculate_timeout_with_equipment(
                base_timeout_seconds=base_timeout_duration, equipment=equipment
            )

            if final_timeout == 0:
                no_timeout_message = f"🛡️ @{command_roll.display_name}, {protection_message}"

                with self._unit_of_work_factory.create() as uow:
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.user_name,
                        content=user_message,
                        current_time=command_roll.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_roll.channel_name,
                        user_name=command_roll.bot_nick,
                        content=no_timeout_message,
                        current_time=command_roll.occurred_at,
                    )
                messages.append(no_timeout_message)
            else:
                reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                timeout_action = RollTimeoutAction(
                    user_name=command_roll.display_name,
                    duration_seconds=final_timeout,
                    reason=reason,
                )
        elif self._is_miss(result_type):
            no_timeout_message = f"✨ @{command_roll.display_name}, редкий эмодзи спас от таймаута!"
            messages.append(no_timeout_message)

        return RollUseCaseResult(messages=messages, timeout_action=timeout_action, new_last_roll_time=new_last_roll_time)

    @staticmethod
    def _is_miss(result_type: str) -> bool:
        return result_type == "miss"

    @staticmethod
    def _is_jackpot(result_type: str) -> bool:
        return result_type == "jackpot"

    @staticmethod
    def _is_partial_match(result_type: str) -> bool:
        return result_type == "partial"

    def _get_result_emoji(self, result_type: str) -> str:
        if self._is_jackpot(result_type):
            return "🎰"
        if self._is_partial_match(result_type):
            return "✨"
        if self._is_miss(result_type):
            return "💥"
        return "💰"

    def _get_profit_display(self, profit: int) -> str:
        if profit > 0:
            return f"+{profit}"
        if profit < 0:
            return f"{profit}"
        return "±0"
