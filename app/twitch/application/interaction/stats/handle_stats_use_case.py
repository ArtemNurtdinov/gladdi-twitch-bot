from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.battle.application.battle_use_case_provider import BattleUseCaseProvider
from app.battle.domain.models import UserBattleStats
from app.betting.application.betting_service import BettingService
from app.betting.presentation.betting_schemas import UserBetStats
from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.twitch.application.interaction.stats.model import StatsDTO
from core.provider import Provider


class HandleStatsUseCase:

    def __init__(
        self,
        economy_service_provider: Provider[EconomyService],
        betting_service_provider: Provider[BettingService],
        battle_use_case_provider: BattleUseCaseProvider,
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        self._economy_service_provider = economy_service_provider
        self._betting_service_provider = betting_service_provider
        self._battle_use_case_provider = battle_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        command_stats: StatsDTO,
    ) -> str:
        with db_session_provider() as db:
            balance = self._economy_service_provider.get(db).get_user_balance(command_stats.channel_name, command_stats.user_name)
            bets = self._betting_service_provider.get(db).get_user_bets(command_stats.channel_name, command_stats.user_name)

        if not bets:
            bet_stats = UserBetStats(total_bets=0, jackpots=0, jackpot_rate=0)
        else:
            total_bets = len(bets)
            jackpots = sum(1 for bet in bets if bet.result_type == "jackpot")
            jackpot_rate = (jackpots / total_bets) * 100 if total_bets > 0 else 0
            bet_stats = UserBetStats(total_bets=total_bets, jackpots=jackpots, jackpot_rate=jackpot_rate)

        with db_readonly_session_provider() as db:
            battles = self._battle_use_case_provider.get(db).get_user_battles(
                channel_name=command_stats.channel_name,
                user_name=command_stats.display_name
            )

        if not battles:
            battle_stats = UserBattleStats(total_battles=0, wins=0, losses=0, win_rate=0.0)
        else:
            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == command_stats.display_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0
            battle_stats = UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)

        result = f"📊 Статистика @{command_stats.display_name}:  💰 Баланс: {balance.balance} монет."

        if bet_stats.total_bets > 0:
            result += f" 🎰 Ставки: {bet_stats.total_bets} | Джекпоты: {bet_stats.jackpots} ({bet_stats.jackpot_rate:.1f}%)."

        if battle_stats.has_battles():
            result += f" ⚔️ Битвы: {battle_stats.total_battles} | Побед: {battle_stats.wins} ({battle_stats.win_rate:.1f}%)."

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_stats.channel_name,
                user_name=command_stats.bot_nick,
                content=result,
                current_time=command_stats.occurred_at,
            )

        return result
