import asyncio
import logging
import random
from datetime import datetime

from app.economy.domain.models import JackpotPayoutMultiplierEffect, PartialPayoutMultiplierEffect, MissPayoutMultiplierEffect, \
    TransactionType
from core.db import SessionLocal, db_ro_session
from app.betting.domain.betting_service import BettingService
from app.betting.domain.models import EmojiConfig, RarityLevel
from typing import Callable

logger = logging.getLogger(__name__)


class RollCommandHandler:
    """Обработчик команды ставки/слот-машины."""

    def __init__(
        self,
        economy_service_factory,
        betting_service_factory,
        equipment_service_factory,
        chat_use_case_factory,
        roll_cooldowns: dict,
        cooldown_seconds: int,
        split_text_fn,
        get_result_emoji_fn,
        get_profit_display_fn,
        is_consolation_prize_fn,
        is_miss_fn,
        timeout_fn,
        command_name: str,
        prefix: str,
        nick_provider: Callable[[], str],
    ):
        self._economy_service = economy_service_factory
        self._betting_service = betting_service_factory
        self._equipment_service = equipment_service_factory
        self._chat_use_case = chat_use_case_factory
        self.roll_cooldowns = roll_cooldowns
        self.cooldown_seconds = cooldown_seconds
        self.split_text = split_text_fn
        self.get_result_emoji = get_result_emoji_fn
        self.get_profit_display = get_profit_display_fn
        self.is_consolation_prize = is_consolation_prize_fn
        self.is_miss = is_miss_fn
        self.timeout_user = timeout_fn
        self.command_name = command_name
        self.prefix = prefix
        self.nick_provider = nick_provider

    async def handle(self, ctx, amount: str | None = None):
        channel_name = ctx.channel.name
        nickname = ctx.author.display_name

        bet_amount = BettingService.BET_COST
        if amount:
            try:
                bet_amount = int(amount)
            except ValueError:
                result = (
                    f"@{nickname}, неверная сумма ставки! Используй: {self.prefix}{self.command_name} [сумма] "
                    f"(например: {self.prefix}{self.command_name} 100). "
                    f"Диапазон: {BettingService.MIN_BET_AMOUNT}-{BettingService.MAX_BET_AMOUNT} монет."
                )
                bot_nick = self.nick_provider() or ""
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
                return

        logger.info(f"Команда {self.command_name} от пользователя {nickname}, сумма ставки: {bet_amount}")

        current_time = datetime.now()
        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, nickname.lower())
            cooldown_seconds = self._equipment_service(db).calculate_roll_cooldown_seconds(self.cooldown_seconds, equipment)

        if nickname in self.roll_cooldowns:
            time_since_last = (current_time - self.roll_cooldowns[nickname]).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{nickname}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                logger.info(f"Пользователь {nickname} попытался использовать команду в кулдауне. Осталось: {remaining_time:.0f} сек")
                bot_nick = self.nick_provider() or ""
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
                return

        self.roll_cooldowns[nickname] = current_time
        logger.debug(f"Обновлен кулдаун для пользователя {nickname}: {current_time}")

        emojis = EmojiConfig.get_emojis_list()
        weights = EmojiConfig.get_weights_list()

        slot_results = random.choices(emojis, weights=weights, k=3)
        slot_result_string = EmojiConfig.format_slot_result(slot_results)

        logger.info(f"Результат слот-машины для {nickname}: {slot_result_string}")

        unique_results = set(slot_results)

        if len(unique_results) == 1:
            result_type = "jackpot"
        elif len(unique_results) == 2:
            result_type = "partial"
        else:
            result_type = "miss"

        normalized_user_name = nickname.lower()

        if bet_amount < BettingService.MIN_BET_AMOUNT:
            result = f"Минимальная сумма ставки: {BettingService.MIN_BET_AMOUNT} монет."
            bot_nick = self.nick_provider() or ""
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if bet_amount > BettingService.MAX_BET_AMOUNT:
            result = f"Максимальная сумма ставки: {BettingService.MAX_BET_AMOUNT} монет."
            bot_nick = self.nick_provider() or ""
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with db_ro_session() as db:
            rarity_level = self._betting_service(db).determine_correct_rarity(slot_result_string, result_type)
            equipment = self._equipment_service(db).get_user_equipment(channel_name, normalized_user_name)

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).subtract_balance(
                channel_name,
                normalized_user_name,
                bet_amount,
                TransactionType.BET_LOSS,
                f"Ставка в слот-машине: {slot_result_string}"
            )
            if not user_balance:
                result = f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет."
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
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
                    channel_name, normalized_user_name, payout, transaction_type, description
                )
            self._betting_service(db).save_bet(channel_name, normalized_user_name, slot_result_string, result_type, rarity_level)

        result_emoji = self.get_result_emoji(result_type, payout)

        economic_info = f" {result_emoji} Баланс: {user_balance.balance} монет"

        profit = payout - bet_amount

        profit_display = self.get_profit_display(result_type, payout, profit)

        economic_info += f" ({profit_display})"

        final_result = f"{slot_result_string} {economic_info}"

        with SessionLocal.begin() as db:
            bot_nick = self.nick_provider() or ""
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), final_result, datetime.utcnow())

        messages = self.split_text(final_result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        if timeout_seconds is not None and timeout_seconds > 0:
            base_timeout_duration = timeout_seconds if timeout_seconds else 0

            with db_ro_session() as db:
                equipment = self._equipment_service(db).get_user_equipment(channel_name, nickname.lower())
                final_timeout, protection_message = self._equipment_service(db).calculate_timeout_with_equipment(
                    nickname,
                    base_timeout_duration,
                    equipment
                )

            if final_timeout == 0:
                if self.is_consolation_prize(result_type, payout):
                    no_timeout_message = f"🎁 @{nickname}, {protection_message} Консольный приз: {payout} монет"
                else:
                    no_timeout_message = f"🛡️ @{nickname}, {protection_message}"

                with SessionLocal.begin() as db:
                    bot_nick = self.nick_provider() or ""
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), no_timeout_message, datetime.utcnow())

                messages = self.split_text(no_timeout_message)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)
            else:
                if self.is_consolation_prize(result_type, payout):
                    reason = f"Промах с редким эмодзи! Консольный приз: {payout} монет. Таймаут: {final_timeout} сек ⏰"
                else:
                    reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                messages = self.split_text(reason)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)

                await self.timeout_user(ctx, nickname, final_timeout, reason)
        elif self.is_miss(result_type):
            if self.is_consolation_prize(result_type, payout):
                no_timeout_message = f"🎁 @{nickname}, повезло! Редкий эмодзи спас от таймаута! Консольный приз: {payout} монет"
            else:
                no_timeout_message = f"✨ @{nickname}, редкий эмодзи спас от таймаута!"

            messages = self.split_text(no_timeout_message)
            for msg in messages:
                await ctx.send(msg)
                await asyncio.sleep(0.3)

