import asyncio
import logging
import random
from datetime import datetime

from core.db import SessionLocal, db_ro_session
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from typing import Callable

logger = logging.getLogger(__name__)


class BattleCommandHandler:
    """Обработчик команды битвы."""

    def __init__(
        self,
        bot,
        economy_service_factory,
        chat_use_case_factory,
        ai_conversation_use_case_factory,
        battle_use_case_factory,
        equipment_service_factory,
        split_text_fn,
        timeout_fn,
        command_name: str,
        prefix: str,
        generate_response_fn,
        nick_provider: Callable[[], str],
    ):
        self.bot = bot
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self._ai_conversation_use_case = ai_conversation_use_case_factory
        self._battle_use_case = battle_use_case_factory
        self._equipment_service = equipment_service_factory
        self.split_text = split_text_fn
        self.timeout_user = timeout_fn
        self.command_name = command_name
        self.prefix = prefix
        self.generate_response_in_chat = generate_response_fn
        self.nick_provider = nick_provider

    async def handle(self, ctx, battle_waiting_user_ref):
        channel_name = ctx.channel.name
        challenger = ctx.author.display_name

        logger.info(f"Команда {self.command_name} от пользователя {challenger}")

        fee = EconomyService.BATTLE_ENTRY_FEE

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, challenger)

        if user_balance.balance < fee:
            result = f"@{challenger}, недостаточно монет для участия в битве! Необходимо: {EconomyService.BATTLE_ENTRY_FEE} монет."
            with SessionLocal.begin() as db:
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if not battle_waiting_user_ref["value"]:
            error_result = None
            with SessionLocal.begin() as db:
                user_balance = self._economy_service(db).subtract_balance(
                    channel_name,
                    challenger,
                    fee,
                    TransactionType.BATTLE_PARTICIPATION,
                    "Участие в битве",
                )
                if not user_balance:
                    error_result = f"@{challenger}, произошла ошибка при списании взноса за битву."
                    bot_nick = self.nick_provider() or ""
                    self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), error_result, datetime.utcnow())

            if error_result:
                await ctx.send(error_result)
                return

            battle_waiting_user_ref["value"] = challenger
            result = (
                f"@{challenger} ищет себе оппонента для эпичной битвы! Взнос: {EconomyService.BATTLE_ENTRY_FEE} монет. "
                f"Используй {self.prefix}{self.command_name}, чтобы принять вызов."
            )
            logger.info(f"{challenger} ищет оппонента для битвы")
            with SessionLocal.begin() as db:
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if battle_waiting_user_ref["value"] == challenger:
            result = f"@{challenger}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            logger.warning(f"{challenger} пытается сражаться сам с собой")
            with SessionLocal.begin() as db:
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            challenger_balance = self._economy_service(db).subtract_balance(
                channel_name,
                challenger,
                fee,
                TransactionType.BATTLE_PARTICIPATION,
                "Участие в битве",
            )
        if not challenger_balance:
            result = f"@{challenger}, произошла ошибка при списании взноса за битву."
            with SessionLocal.begin() as db:
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        opponent = battle_waiting_user_ref["value"]
        battle_waiting_user_ref["value"] = None

        logger.info(f"Начинается битва между {opponent} и {challenger}")

        prompt = (
            f"На арене сражаются два героя: {opponent} и {challenger}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
        )

        with db_ro_session() as db:
            opponent_equipment = self._equipment_service(db).get_user_equipment(channel_name, opponent.lower())
            challenger_equipment = self._equipment_service(db).get_user_equipment(channel_name, challenger.lower())
            if opponent_equipment:
                equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in opponent_equipment]
                prompt += f"\nВооружение {opponent}: {', '.join(equipment_details)}."
            if challenger_equipment:
                equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in challenger_equipment]
                prompt += f"\nВооружение {challenger}: {', '.join(equipment_details)}."

        winner = random.choice([opponent, challenger])
        loser = challenger if winner == opponent else opponent

        prompt += (
            "\nБитва должна быть короткой, но эпичной и красочной."
            f"\nПобедить в битве должен {winner}, проигравший: {loser}"
            f"\n\nПроигравший получит таймаут! Победитель получит {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        )

        result = self.generate_response_in_chat(prompt, channel_name)

        logger.info(f"Битва завершена. Победитель: {winner}")

        winner_amount = EconomyService.BATTLE_WINNER_PRIZE
        with SessionLocal.begin() as db:
            self._economy_service(db).add_balance(
                channel_name, winner, winner_amount, TransactionType.BATTLE_WIN, f"Победа в битве против {loser}"
            )
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            bot_nick = self.nick_provider() or ""
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            self._battle_use_case(db).save_battle_history(channel_name, opponent, challenger, winner, result)

        messages = self.split_text(result)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        logger.info(f"Проигравший: {loser}, получает таймаут")

        winner_message = f"{winner} получает {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        await ctx.send(winner_message)

        with SessionLocal.begin() as db:
            bot_nick = self.nick_provider() or ""
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), winner_message, datetime.utcnow())
        await asyncio.sleep(1)

        base_battle_timeout = 120
        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, loser.lower())
            final_timeout, protection_message = self._equipment_service(db).calculate_timeout_with_equipment(
                loser, base_battle_timeout, equipment
            )

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            await ctx.send(no_timeout_message)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), no_timeout_message, datetime.utcnow())
        else:
            timeout_minutes = final_timeout // 60
            timeout_seconds_remainder = final_timeout % 60

            if timeout_minutes > 0:
                time_display = (
                    f"{timeout_minutes} минут"
                    if timeout_seconds_remainder == 0
                    else f"{timeout_minutes}м {timeout_seconds_remainder}с"
                )
            else:
                time_display = f"{timeout_seconds_remainder} секунд"

            reason = f"Поражение в битве! Время на тренировки: {time_display}"

            if protection_message:
                reason += f" {protection_message}"

            await self.timeout_user(ctx, loser, final_timeout, reason)

