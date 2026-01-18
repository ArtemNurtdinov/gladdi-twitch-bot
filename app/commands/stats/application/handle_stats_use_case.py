from app.battle.domain.models import UserBattleStats
from app.commands.stats.application.model import StatsDTO, UserBetStats
from app.commands.stats.application.stats_uow import StatsUnitOfWorkFactory


class HandleStatsUseCase:
    def __init__(
        self,
        unit_of_work_factory: StatsUnitOfWorkFactory,
    ):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(
        self,
        command_stats: StatsDTO,
    ) -> str:
        user_message = command_stats.command_prefix + command_stats.command_name

        with self._unit_of_work_factory.create(read_only=True) as uow:
            balance = uow.economy_policy.get_user_balance(command_stats.channel_name, command_stats.user_name)
            bets = uow.betting_service.get_user_bets(command_stats.channel_name, command_stats.user_name)

        if not bets:
            bet_stats = UserBetStats(total_bets=0, jackpots=0, jackpot_rate=0)
        else:
            total_bets = len(bets)
            jackpots = sum(1 for bet in bets if bet.result_type == "jackpot")
            jackpot_rate = (jackpots / total_bets) * 100 if total_bets > 0 else 0
            bet_stats = UserBetStats(total_bets=total_bets, jackpots=jackpots, jackpot_rate=jackpot_rate)

        with self._unit_of_work_factory.create(read_only=True) as uow:
            battles = uow.battle_use_case.get_user_battles(
                channel_name=command_stats.channel_name, user_name=command_stats.display_name
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

        if battle_stats.total_battles > 0:
            result += f" ⚔️ Битвы: {battle_stats.total_battles} | Побед: {battle_stats.wins} ({battle_stats.win_rate:.1f}%)."

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_stats.channel_name,
                user_name=command_stats.user_name,
                content=user_message,
                current_time=command_stats.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_stats.channel_name,
                user_name=command_stats.bot_nick,
                content=result,
                current_time=command_stats.occurred_at,
            )
        return result
