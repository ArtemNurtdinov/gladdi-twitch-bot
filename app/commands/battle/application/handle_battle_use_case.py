import random

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.commands.battle.application.battle_uow import BattleUnitOfWorkFactory
from app.commands.battle.application.model import BattleDTO, BattleTimeoutAction, BattleUseCaseResult
from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.domain.models import TransactionType
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from core.provider import SingletonProvider


class HandleBattleUseCase:
    def __init__(
        self,
        unit_of_work_factory: BattleUnitOfWorkFactory,
        chat_response_use_case: ChatResponseUseCase,
        calculate_timeout_use_case_provider: SingletonProvider[CalculateTimeoutUseCase],
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._chat_response_use_case = chat_response_use_case
        self._calculate_timeout_use_case_provider = calculate_timeout_use_case_provider

    async def handle(
        self,
        command_battle: BattleDTO,
    ) -> BattleUseCaseResult:
        challenger_display = command_battle.display_name
        challenger_user = command_battle.user_name
        bot_nick = command_battle.bot_nick
        user_message = command_battle.command_prefix + command_battle.command_name

        fee = EconomyPolicy.BATTLE_ENTRY_FEE

        with self._unit_of_work_factory.create(read_only=True) as uow:
            user_balance = uow.economy_policy.get_user_balance(
                channel_name=command_battle.channel_name, user_name=challenger_user
            )

        if user_balance.balance < fee:
            result = f"@{challenger_display}, недостаточно монет для участия в битве! Необходимо: {EconomyPolicy.BATTLE_ENTRY_FEE} монет."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.user_name,
                    content=user_message,
                    current_time=command_battle.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=command_battle.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=command_battle.waiting_user,
                timeout_action=None,
            )

        if not command_battle.waiting_user:
            error_result = None
            with self._unit_of_work_factory.create() as uow:
                user_balance = uow.economy_policy.subtract_balance(
                    channel_name=command_battle.channel_name,
                    user_name=challenger_user,
                    amount=fee,
                    transaction_type=TransactionType.BATTLE_PARTICIPATION,
                    description="Участие в битве",
                )
                if not user_balance:
                    error_result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_battle.channel_name,
                        user_name=command_battle.user_name,
                        content=user_message,
                        current_time=command_battle.occurred_at,
                    )
                    uow.chat_use_case.save_chat_message(
                        channel_name=command_battle.channel_name,
                        user_name=bot_nick,
                        content=error_result,
                        current_time=command_battle.occurred_at,
                    )

            if error_result:
                return BattleUseCaseResult(
                    messages=[error_result],
                    new_waiting_user=command_battle.waiting_user,
                    timeout_action=None,
                )

            result = (
                f"@{challenger_display} ищет себе оппонента для эпичной битвы! "
                f"Взнос: {EconomyPolicy.BATTLE_ENTRY_FEE} монет. "
                f"Используй {command_battle.command_call}, чтобы принять вызов."
            )
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.user_name,
                    content=user_message,
                    current_time=command_battle.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=command_battle.occurred_at,
                )

            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=challenger_display,
                timeout_action=None,
            )

        if command_battle.waiting_user == challenger_display:
            result = f"@{challenger_display}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.user_name,
                    content=user_message,
                    current_time=command_battle.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=command_battle.occurred_at,
                )
            return BattleUseCaseResult(
                messages=[result],
                new_waiting_user=command_battle.waiting_user,
                timeout_action=None,
            )

        with self._unit_of_work_factory.create() as uow:
            challenger_balance = uow.economy_policy.subtract_balance(
                channel_name=command_battle.channel_name,
                user_name=challenger_user,
                amount=fee,
                transaction_type=TransactionType.BATTLE_PARTICIPATION,
                description="Участие в битве",
            )
        if not challenger_balance:
            result = f"@{challenger_display}, произошла ошибка при списании взноса за битву."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.user_name,
                    content=user_message,
                    current_time=command_battle.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=bot_nick,
                    content=result,
                    current_time=command_battle.occurred_at,
                )
            return BattleUseCaseResult(messages=[result], new_waiting_user=command_battle.waiting_user, timeout_action=None)

        opponent_display = command_battle.waiting_user
        new_waiting_user = None

        winner = random.choice([opponent_display, challenger_display])
        loser = challenger_display if winner == opponent_display else opponent_display

        prompt = (
            f"На арене сражаются два героя: {opponent_display} и {challenger_display}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
            "\nБитва должна быть короткой, но эпичной и красочной."
            f"\nПобедить в битве должен {winner}, проигравший: {loser}"
            f"\n\nПроигравший получит таймаут! Победитель получит {EconomyPolicy.BATTLE_WINNER_PRIZE} монет!"
        )

        result_story = await self._chat_response_use_case.generate_response(prompt, command_battle.channel_name)

        winner_amount = EconomyPolicy.BATTLE_WINNER_PRIZE
        with self._unit_of_work_factory.create() as uow:
            uow.economy_policy.add_balance(
                channel_name=command_battle.channel_name,
                user_name=winner,
                amount=winner_amount,
                transaction_type=TransactionType.BATTLE_WIN,
                description=f"Победа в битве против {loser}",
            )
            uow.conversation_service.save_conversation_to_db(
                channel_name=command_battle.channel_name, user_message=prompt, ai_message=result_story
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=command_battle.user_name,
                content=user_message,
                current_time=command_battle.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=bot_nick,
                content=result_story,
                current_time=command_battle.occurred_at,
            )
            uow.battle_use_case.save_battle_history(
                channel_name=command_battle.channel_name,
                opponent_1=opponent_display,
                opponent_2=challenger_display,
                winner=winner,
                result_text=result_story,
            )

        messages = [result_story]

        winner_message = f"{winner} получает {EconomyPolicy.BATTLE_WINNER_PRIZE} монет!"
        messages.append(winner_message)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=bot_nick,
                content=winner_message,
                current_time=command_battle.occurred_at,
            )

        base_battle_timeout = 120
        with self._unit_of_work_factory.create(read_only=True) as uow:
            equipment = uow.get_user_equipment_use_case.get_user_equipment(
                channel_name=command_battle.channel_name, user_name=loser.lower()
            )

        final_timeout, protection_message = self._calculate_timeout_use_case_provider.get().calculate_timeout_with_equipment(
            base_timeout_seconds=base_battle_timeout, equipment=equipment
        )

        timeout_action = None
        delay_before_timeout = 1.0

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            messages.append(no_timeout_message)
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=bot_nick,
                    content=no_timeout_message,
                    current_time=command_battle.occurred_at,
                )
        else:
            timeout_minutes = final_timeout // 60
            timeout_seconds_remainder = final_timeout % 60
            if timeout_minutes > 0:
                time_display = (
                    f"{timeout_minutes} минут" if timeout_seconds_remainder == 0 else f"{timeout_minutes}м {timeout_seconds_remainder}с"
                )
            else:
                time_display = f"{timeout_seconds_remainder} секунд"

            reason = f"Поражение в битве! Время на тренировки: {time_display}"

            if protection_message:
                reason += f" {protection_message}"

            timeout_action = BattleTimeoutAction(user_name=loser, duration_seconds=final_timeout, reason=reason)

        return BattleUseCaseResult(
            messages=messages,
            new_waiting_user=new_waiting_user,
            timeout_action=timeout_action,
            delay_before_timeout=delay_before_timeout,
        )
