import random
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.equipment.domain.equipment_service import EquipmentService
from app.twitch.application.interaction.battle.dto import BattleDTO, BattleUseCaseResult, BattleTimeoutAction


class HandleBattleUseCase:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        battle_use_case_factory: Callable[[Session], BattleUseCase],
        equipment_service_factory: Callable[[Session], EquipmentService],
        generate_response_fn: Callable[[str, str], str],
    ):
        self._economy_service_factory = economy_service_factory
        self._chat_use_case_factory = chat_use_case_factory
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._battle_use_case_factory = battle_use_case_factory
        self._equipment_service_factory = equipment_service_factory
        self._generate_response_fn = generate_response_fn

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: BattleDTO,
    ) -> BattleUseCaseResult:
        challenger_display = dto.display_name
        challenger_user = dto.user_name
        bot_nick = dto.bot_nick

        fee = EconomyService.BATTLE_ENTRY_FEE

        with db_session_provider() as db:
            user_balance = self._economy_service_factory(db).get_user_balance(dto.channel_name, challenger_user)

        if user_balance.balance < fee:
            result = (
                f"@{challenger_display}, недостаточно монет для участия в битве! "
                f"Необходимо: {EconomyService.BATTLE_ENTRY_FEE} монет."
            )
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=dto.waiting_user,
                timeout_action=None,
            )

        if not dto.waiting_user:
            error_result = None
            with db_session_provider() as db:
                user_balance = self._economy_service_factory(db).subtract_balance(
                    channel_name=dto.channel_name,
                    user_name=challenger_user,
                    amount=fee,
                    transaction_type=TransactionType.BATTLE_PARTICIPATION,
                    description="Участие в битве",
                )
                if not user_balance:
                    error_result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
                    self._chat_use_case_factory(db).save_chat_message(
                        channel_name=dto.channel_name,
                        user_name=bot_nick,
                        content=error_result,
                        current_time=dto.occurred_at,
                    )

            if error_result:
                return BattleUseCaseResult(
                    messages=[error_result],
                    new_waiting_user=dto.waiting_user,
                    timeout_action=None,
                )

            result = (
                f"@{challenger_display} ищет себе оппонента для эпичной битвы! "
                f"Взнос: {EconomyService.BATTLE_ENTRY_FEE} монет. "
                f"Используй {dto.command_call}, чтобы принять вызов."
            )
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=dto.occurred_at,
                )

            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=challenger_display,
                timeout_action=None,
            )

        if dto.waiting_user == challenger_display:
            result = f"@{challenger_display}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=dto.waiting_user,
                timeout_action=None,
            )

        with db_session_provider() as db:
            challenger_balance = self._economy_service_factory(db).subtract_balance(
                channel_name=dto.channel_name,
                user_name=challenger_user,
                amount=fee,
                transaction_type=TransactionType.BATTLE_PARTICIPATION,
                description="Участие в битве",
            )
        if not challenger_balance:
            result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=dto.waiting_user,
                timeout_action=None,
            )

        opponent_display = dto.waiting_user
        new_waiting_user = None

        prompt = (
            f"На арене сражаются два героя: {opponent_display} и {challenger_display}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
        )

        with db_readonly_session_provider() as db:
            opponent_equipment = self._equipment_service_factory(db).get_user_equipment(dto.channel_name, opponent_display.lower())
            challenger_equipment = self._equipment_service_factory(db).get_user_equipment(dto.channel_name, challenger_user)
        if opponent_equipment:
            equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in opponent_equipment]
            prompt += f"\nВооружение {opponent_display}: {', '.join(equipment_details)}."
        if challenger_equipment:
            equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in challenger_equipment]
            prompt += f"\nВооружение {challenger_display}: {', '.join(equipment_details)}."

        winner = random.choice([opponent_display, challenger_display])
        loser = challenger_display if winner == opponent_display else opponent_display

        prompt += (
            "\nБитва должна быть короткой, но эпичной и красочной."
            f"\nПобедить в битве должен {winner}, проигравший: {loser}"
            f"\n\nПроигравший получит таймаут! Победитель получит {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        )

        result_story = self._generate_response_fn(prompt, dto.channel_name)

        winner_amount = EconomyService.BATTLE_WINNER_PRIZE
        with db_session_provider() as db:
            self._economy_service_factory(db).add_balance(
                dto.channel_name,
                winner,
                winner_amount,
                TransactionType.BATTLE_WIN,
                f"Победа в битве против {loser}",
            )
            self._ai_conversation_use_case_factory(db).save_conversation_to_db(dto.channel_name, prompt, result_story)
            self._chat_use_case_factory(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=bot_nick,
                content=result_story,
                current_time=dto.occurred_at,
            )
            self._battle_use_case_factory(db).save_battle_history(
                dto.channel_name, opponent_display, challenger_display, winner, result_story
            )

        messages = [result_story]

        winner_message = f"{winner} получает {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        messages.append(winner_message)

        with db_session_provider() as db:
            self._chat_use_case_factory(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=bot_nick,
                content=winner_message,
                current_time=dto.occurred_at,
            )

        base_battle_timeout = 120
        with db_readonly_session_provider() as db:
            equipment = self._equipment_service_factory(db).get_user_equipment(dto.channel_name, loser.lower())
            final_timeout, protection_message = self._equipment_service_factory(db).calculate_timeout_with_equipment(
                base_timeout_seconds=base_battle_timeout,
                equipment=equipment
            )

        timeout_action = None
        delay_before_timeout = 1.0

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            messages.append(no_timeout_message)
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(
                    channel_name=dto.channel_name,
                    user_name=bot_nick,
                    content=no_timeout_message,
                    current_time=dto.occurred_at,
                )
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

            timeout_action = BattleTimeoutAction(
                user_name=loser,
                duration_seconds=final_timeout,
                reason=reason,
            )

        return BattleUseCaseResult(
            messages=messages,
            new_waiting_user=new_waiting_user,
            timeout_action=timeout_action,
            delay_before_timeout=delay_before_timeout,
        )

