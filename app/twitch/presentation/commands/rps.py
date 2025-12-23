from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.minigame.domain.models import RPS_CHOICES
from app.minigame.domain.minigame_service import MinigameService
from core.db import SessionLocal


class RpsCommandHandler:

    def __init__(
        self,
        minigame_service: MinigameService,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.minigame_service = minigame_service
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.nick_provider = nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, display_name: str, ctx, choice: str | None):
        user_name = display_name.lower()
        bot_nick = (self.nick_provider() or "").lower()

        if not choice:
            await self.post_message_fn(f"@{display_name}, укажите ваш выбор: камень / ножницы / бумага", ctx)
            return

        rps_game_is_active = self.minigame_service.rps_game_is_active(channel_name)
        if not rps_game_is_active:
            message = "Сейчас нет активной игры 'камень-ножницы-бумага'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        game = self.minigame_service.get_active_rps_game(channel_name)

        if datetime.utcnow() > game.end_time:
            bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game, channel_name)
            if winners:
                share = max(1, game.bank // len(winners))
                with SessionLocal.begin() as db:
                    for winner in winners:
                        self._economy_service(db).add_balance(
                            channel_name,
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
                message = (
                    f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. "
                    f"Банк {game.bank} монет сгорает."
                )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        normalized_choice = choice.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            message = "Выберите: камень, ножницы или бумага"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        if game.user_choices and game.user_choices.get(user_name):
            existing = game.user_choices[user_name]
            message = f"Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        fee = MinigameService.RPS_ENTRY_FEE_PER_USER

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).subtract_balance(
                channel_name,
                user_name,
                fee,
                TransactionType.SPECIAL_EVENT,
                "Участие в игре 'камень-ножницы-бумага'",
            )
        if not user_balance:
            message = f"Недостаточно средств! Требуется {fee} монет"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
            await self.post_message_fn(message, ctx)
            return

        game.bank += fee
        game.user_choices[user_name] = choice

        message = f"Принято: @{display_name} — {normalized_choice}"
        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, message, datetime.utcnow())
        await self.post_message_fn(message, ctx)


