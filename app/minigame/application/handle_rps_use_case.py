from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.minigame.application.model import RpsDTO
from app.minigame.domain.minigame_service import MinigameService
from app.minigame.domain.models import RPS_CHOICES
from core.provider import Provider


class HandleRpsUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        economy_service_provider: Provider[EconomyService],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        self._minigame_service = minigame_service
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        dto: RpsDTO,
    ) -> str:
        bot_nick = dto.bot_nick
        user_name = dto.user_name

        if not dto.choice_input:
            return f"@{dto.display_name}, укажите ваш выбор: камень / ножницы / бумага"

        rps_game_is_active = self._minigame_service.rps_game_is_active(dto.channel_name)
        if not rps_game_is_active:
            message = "Сейчас нет активной игры 'камень-ножницы-бумага'"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        game = self._minigame_service.get_active_rps_game(dto.channel_name)

        if datetime.utcnow() > game.end_time:
            bot_choice, winning_choice, winners = self._minigame_service.finish_rps(game, dto.channel_name)
            if winners:
                share = max(1, game.bank // len(winners))
                with db_session_provider() as db:
                    for winner in winners:
                        self._economy_service_provider.get(db).add_balance(
                            dto.channel_name,
                            winner,
                            share,
                            TransactionType.MINIGAME_WIN,
                            f"Победа в КНБ ({winning_choice})",
                        )
                winners_display = ", ".join(f"@{winner}" for winner in winners)
                message = (
                    f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. "
                    f"Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
                )
            else:
                message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        normalized_choice = dto.choice_input.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            message = "Выберите: камень, ножницы или бумага"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        if game.user_choices and game.user_choices.get(user_name):
            existing = game.user_choices[user_name]
            message = f"Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        fee = MinigameService.RPS_ENTRY_FEE_PER_USER

        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).subtract_balance(
                channel_name=dto.channel_name,
                user_name=user_name,
                amount=fee,
                transaction_type=TransactionType.SPECIAL_EVENT,
                description="Участие в игре 'камень-ножницы-бумага'",
            )
        if not user_balance:
            message = f"Недостаточно средств! Требуется {fee} монет"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
            return message

        game.bank += fee
        game.user_choices[user_name] = normalized_choice

        message = f"Принято: @{dto.display_name} — {normalized_choice}"
        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, message, dto.occurred_at)
        return message
