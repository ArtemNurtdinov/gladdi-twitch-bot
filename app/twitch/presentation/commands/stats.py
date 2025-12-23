import asyncio
from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case import BattleUseCase
from app.battle.domain.models import UserBattleStats
from app.betting.domain.betting_service import BettingService
from app.betting.presentation.betting_schemas import UserBetStats
from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from core.db import SessionLocal, db_ro_session


class StatsCommandHandler:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        betting_service_factory: Callable[[Session], BettingService],
        battle_use_case_factory: Callable[[Session], BattleUseCase],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_name: str,
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._economy_service = economy_service_factory
        self._betting_service = betting_service_factory
        self._battle_use_case = battle_use_case_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        normalized_user_name = user_name.lower()
        bot_nick = self.nick_provider() or ""

        with SessionLocal.begin() as db:
            balance = self._economy_service(db).get_user_balance(channel_name, normalized_user_name)
            bets = self._betting_service(db).get_user_bets(channel_name, normalized_user_name)

        if not bets:
            bet_stats = UserBetStats(total_bets=0, jackpots=0, jackpot_rate=0)
        else:
            total_bets = len(bets)
            jackpots = sum(1 for bet in bets if bet.result_type == "jackpot")
            jackpot_rate = (jackpots / total_bets) * 100 if total_bets > 0 else 0
            bet_stats = UserBetStats(total_bets=total_bets, jackpots=jackpots, jackpot_rate=jackpot_rate)

        with db_ro_session() as db:
            battles = self._battle_use_case(db).get_user_battles(channel_name, user_name)

        if not battles:
            battle_stats = UserBattleStats(total_battles=0, wins=0, losses=0, win_rate=0.0)
        else:
            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == user_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0
            battle_stats = UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)

        result = f"📊 Статистика @{user_name}:  💰 Баланс: {balance.balance} монет."

        if bet_stats.total_bets > 0:
            result += f" 🎰 Ставки: {bet_stats.total_bets} | Джекпоты: {bet_stats.jackpots} ({bet_stats.jackpot_rate:.1f}%)."

        if battle_stats.has_battles():
            result += f" ⚔️ Битвы: {battle_stats.total_battles} | Побед: {battle_stats.wins} ({battle_stats.win_rate:.1f}%)."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)
