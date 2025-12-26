import random
from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case import BattleUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.twitch.application.interaction.battle.dto import BattleDTO, BattleUseCaseResult, BattleTimeoutAction
from app.twitch.application.shared import ChatResponder
from app.twitch.application.shared.battle_use_case_provider import BattleUseCaseProvider
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider
from app.twitch.application.shared.conversation_service_provider import ConversationServiceProvider
from app.twitch.application.shared.economy_service_provider import EconomyServiceProvider
from app.twitch.application.shared.equipment_service_provider import EquipmentServiceProvider


class HandleBattleUseCase:

    def __init__(
        self,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
        conversation_service_provider: ConversationServiceProvider,
        battle_use_case_provider: BattleUseCaseProvider,
        equipment_service_provider: EquipmentServiceProvider,
        chat_responder: ChatResponder,
    ):
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._battle_use_case_provider = battle_use_case_provider
        self._equipment_service_provider = equipment_service_provider
        self._chat_responder = chat_responder

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        battle_dto: BattleDTO,
    ) -> BattleUseCaseResult:
        challenger_display = battle_dto.display_name
        challenger_user = battle_dto.user_name
        bot_nick = battle_dto.bot_nick

        fee = EconomyService.BATTLE_ENTRY_FEE

        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).get_user_balance(battle_dto.channel_name, challenger_user)

        if user_balance.balance < fee:
            result = (
                f"@{challenger_display}, недостаточно монет для участия в битве! "
                f"Необходимо: {EconomyService.BATTLE_ENTRY_FEE} монет."
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=battle_dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=battle_dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=battle_dto.waiting_user,
                timeout_action=None,
            )

        if not battle_dto.waiting_user:
            error_result = None
            with db_session_provider() as db:
                user_balance = self._economy_service_provider.get(db).subtract_balance(
                    channel_name=battle_dto.channel_name,
                    user_name=challenger_user,
                    amount=fee,
                    transaction_type=TransactionType.BATTLE_PARTICIPATION,
                    description="Участие в битве",
                )
                if not user_balance:
                    error_result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
                    self._chat_use_case_provider.get(db).save_chat_message(
                        channel_name=battle_dto.channel_name,
                        user_name=bot_nick,
                        content=error_result,
                        current_time=battle_dto.occurred_at,
                    )

            if error_result:
                return BattleUseCaseResult(
                    messages=[error_result],
                    new_waiting_user=battle_dto.waiting_user,
                    timeout_action=None,
                )

            result = (
                f"@{challenger_display} ищет себе оппонента для эпичной битвы! "
                f"Взнос: {EconomyService.BATTLE_ENTRY_FEE} монет. "
                f"Используй {battle_dto.command_call}, чтобы принять вызов."
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=battle_dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=battle_dto.occurred_at,
                )

            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=challenger_display,
                timeout_action=None,
            )

        if battle_dto.waiting_user == challenger_display:
            result = f"@{challenger_display}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=battle_dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=battle_dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=battle_dto.waiting_user,
                timeout_action=None,
            )

        with db_session_provider() as db:
            challenger_balance = self._economy_service_provider.get(db).subtract_balance(
                channel_name=battle_dto.channel_name,
                user_name=challenger_user,
                amount=fee,
                transaction_type=TransactionType.BATTLE_PARTICIPATION,
                description="Участие в битве",
            )
        if not challenger_balance:
            result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=battle_dto.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=battle_dto.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=battle_dto.waiting_user,
                timeout_action=None,
            )

        opponent_display = battle_dto.waiting_user
        new_waiting_user = None

        prompt = (
            f"На арене сражаются два героя: {opponent_display} и {challenger_display}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
        )

        with db_readonly_session_provider() as db:
            opponent_equipment = self._equipment_service_provider.get(db).get_user_equipment(battle_dto.channel_name, opponent_display.lower())
            challenger_equipment = self._equipment_service_provider.get(db).get_user_equipment(battle_dto.channel_name, challenger_user)
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

        result_story = self._chat_responder.generate_response(prompt, battle_dto.channel_name)

        winner_amount = EconomyService.BATTLE_WINNER_PRIZE
        with db_session_provider() as db:
            self._economy_service_provider.get(db).add_balance(
                battle_dto.channel_name,
                winner,
                winner_amount,
                TransactionType.BATTLE_WIN,
                f"Победа в битве против {loser}",
            )
            self._conversation_service_provider.get(db).save_conversation_to_db(battle_dto.channel_name, prompt, result_story)
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=battle_dto.channel_name,
                user_name=bot_nick,
                content=result_story,
                current_time=battle_dto.occurred_at,
            )
            self._battle_use_case_provider.get(db).save_battle_history(
                battle_dto.channel_name, opponent_display, challenger_display, winner, result_story
            )

        messages = [result_story]

        winner_message = f"{winner} получает {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        messages.append(winner_message)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=battle_dto.channel_name,
                user_name=bot_nick,
                content=winner_message,
                current_time=battle_dto.occurred_at,
            )

        base_battle_timeout = 120
        with db_readonly_session_provider() as db:
            equipment = self._equipment_service_provider.get(db).get_user_equipment(battle_dto.channel_name, loser.lower())
            final_timeout, protection_message = self._equipment_service_provider.get(db).calculate_timeout_with_equipment(
                base_timeout_seconds=base_battle_timeout,
                equipment=equipment
            )

        timeout_action = None
        delay_before_timeout = 1.0

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            messages.append(no_timeout_message)
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=battle_dto.channel_name,
                    user_name=bot_nick,
                    content=no_timeout_message,
                    current_time=battle_dto.occurred_at,
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
