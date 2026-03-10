from datetime import datetime

from app.economy.domain.models import TransactionType
from app.minigame.application.model.rps import RpsDTO
from app.minigame.application.uow.rps_uow import RpsUnitOfWorkFactory
from app.minigame.domain.minigame_service import RPS_CHOICES, MinigameService


class HandleRpsUseCase:
    def __init__(self, minigame_service: MinigameService, rps_uow: RpsUnitOfWorkFactory):
        self._minigame_service = minigame_service
        self._rps_uow = rps_uow

    async def handle(self, rps: RpsDTO) -> str:
        bot_nick = rps.bot_nick
        user_name = rps.user_name

        if not rps.choice_input:
            return f"@{rps.display_name}, укажите ваш выбор: камень / ножницы / бумага"

        user_message = rps.command_prefix + rps.command_name + " " + rps.choice_input

        rps_game_is_active = self._minigame_service.rps_game_is_active(rps.channel_name)
        if not rps_game_is_active:
            message = "Сейчас нет активной игры 'камень-ножницы-бумага'"
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        game = self._minigame_service.get_active_rps_game(rps.channel_name)

        if datetime.utcnow() > game.end_time:
            bot_choice, winning_choice, winners = self._minigame_service.finish_rps(game, rps.channel_name)
            if winners:
                share = max(1, game.bank // len(winners))
                with self._rps_uow.create() as uow:
                    for winner in winners:
                        uow.economy_policy.add_balance(
                            rps.channel_name,
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
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        if not game.is_active:
            message = "Игра уже завершена"
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        normalized_choice = rps.choice_input.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            message = "Выберите: камень, ножницы или бумага"
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        if game.user_choices and game.user_choices.get(user_name):
            existing = game.user_choices[user_name]
            message = f"Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        fee = MinigameService.RPS_ENTRY_FEE_PER_USER

        with self._rps_uow.create() as uow:
            user_balance = uow.economy_policy.subtract_balance(
                channel_name=rps.channel_name,
                user_name=user_name,
                amount=fee,
                transaction_type=TransactionType.SPECIAL_EVENT,
                description="Участие в игре 'камень-ножницы-бумага'",
            )
        if not user_balance:
            message = f"Недостаточно средств! Требуется {fee} монет"
            with self._rps_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
                )
            return message

        game.bank += fee
        game.user_choices[user_name] = normalized_choice

        message = f"Принято: @{rps.display_name} — {normalized_choice}"
        with self._rps_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=rps.channel_name, user_name=rps.user_name, content=user_message, current_time=rps.occurred_at
            )
            uow.chat_use_case.save_chat_message(
                channel_name=rps.channel_name, user_name=bot_nick, content=message, current_time=rps.occurred_at
            )
        return message
