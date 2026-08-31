import asyncio
import random

from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.battle.application.model.join_battle_result import JoinBattleResult
from app.common.infrastructure.db.session_scoped_factory import SessionScopedFactory
from app.common.infrastructure.db.types import SessionFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.domain.models import TransactionType
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.platform.command.battle.application.battle_uow import BattleUnitOfWorkFactory
from app.platform.command.battle.application.model import BattleDTO, BattleTimeoutAction, BattleUseCaseResult


class HandleBattleUseCase:
    def __init__(
        self,
        battle_uow: BattleUnitOfWorkFactory,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        calculate_timeout_use_case: CalculateTimeoutUseCase,
        db_ro_session: SessionFactory,
    ):
        self._battle_uow = battle_uow
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._calculate_timeout_use_case = calculate_timeout_use_case
        self._db_ro_session = db_ro_session
        self._match_lock = asyncio.Lock()
        self._waiting_user: str | None = None

    async def handle(self, command_battle: BattleDTO) -> BattleUseCaseResult:
        async with self._match_lock:
            join_result = self._join_queue(command_battle)
            opponent = join_result.matched_opponent
            if opponent is None:
                return BattleUseCaseResult(messages=join_result.messages, timeout_action=None)

        return await self._resolve_fight(command_battle, opponent)

    def _join_queue(self, command_battle: BattleDTO) -> JoinBattleResult:
        challenger_display = command_battle.display_name
        challenger_user = command_battle.user_name
        fee = EconomyPolicy.BATTLE_ENTRY_FEE

        with self._battle_uow.create(read_only=True) as uow:
            user_balance = uow.economy_policy.get_user_balance(channel_name=command_battle.channel_name, user_name=challenger_user)

        if user_balance.balance < fee:
            result = f"@{challenger_display}, недостаточно монет для участия в битве! Необходимо: {EconomyPolicy.BATTLE_ENTRY_FEE} монет."
            self._save_command_and_reply(command_battle, result)
            return JoinBattleResult(messages=[result], matched_opponent=None)

        if self._waiting_user == challenger_display:
            result = f"@{challenger_display}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            self._save_command_and_reply(command_battle, result)
            return JoinBattleResult(messages=[result], matched_opponent=None)

        with self._battle_uow.create() as uow:
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
                    content=command_battle.message,
                    current_time=command_battle.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.bot_name,
                    content=error_result,
                    current_time=command_battle.occurred_at,
                )
                return JoinBattleResult(messages=[error_result], matched_opponent=None)

        if self._waiting_user is None:
            result = (
                f"@{challenger_display} ищет себе оппонента для эпичной битвы! "
                f"Взнос: {EconomyPolicy.BATTLE_ENTRY_FEE} монет. "
                f"Используй {command_battle.command_call}, чтобы принять вызов."
            )
            self._save_command_and_reply(command_battle, result)
            self._waiting_user = challenger_display
            return JoinBattleResult(messages=[result], matched_opponent=None)

        opponent = self._waiting_user
        self._waiting_user = None
        return JoinBattleResult(messages=[], matched_opponent=opponent)

    def _save_command_and_reply(self, command_battle: BattleDTO, reply: str) -> None:
        with self._battle_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=command_battle.user_name,
                content=command_battle.message,
                current_time=command_battle.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=command_battle.bot_name,
                content=reply,
                current_time=command_battle.occurred_at,
            )

    async def _resolve_fight(self, command_battle: BattleDTO, opponent_display: str) -> BattleUseCaseResult:
        challenger_display = command_battle.display_name

        winner = random.choice([opponent_display, challenger_display])
        loser = challenger_display if winner == opponent_display else opponent_display

        prompt = (
            f"На арене сражаются два героя: {opponent_display} и {challenger_display}."
            "\nСимулируй абсурдную и эпическую битву между ними в одно предложение."
            f"\nПобедить в битве должен {winner}, проигравший: {loser}"
        )

        with self._db_ro_session() as session:
            result_story = await self._generate_response_use_case_factory.get(session).generate_response(
                prompt=prompt, channel_name=command_battle.channel_name
            )

        winner_amount = EconomyPolicy.BATTLE_WINNER_PRIZE
        with self._battle_uow.create() as uow:
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
                content=command_battle.message,
                current_time=command_battle.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=command_battle.bot_name,
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

        winner_message = f"{winner} получает {winner_amount} монет!"
        messages.append(winner_message)

        with self._battle_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_battle.channel_name,
                user_name=command_battle.bot_name,
                content=winner_message,
                current_time=command_battle.occurred_at,
            )

        base_battle_timeout = 120
        with self._battle_uow.create(read_only=True) as uow:
            equipment = uow.get_user_equipment_use_case.get_user_equipment(
                channel_name=command_battle.channel_name, user_name=loser.lower()
            )

        final_timeout, protection_message = self._calculate_timeout_use_case.calculate_timeout_with_equipment(
            base_timeout_seconds=base_battle_timeout, equipment=equipment
        )

        timeout_action = None

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            messages.append(no_timeout_message)
            with self._battle_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_battle.channel_name,
                    user_name=command_battle.bot_name,
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
            timeout_action=timeout_action,
        )
