from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.battle.presentation.battle_command_handler import BattleCommandHandler
from app.commands.follow.followage_command_handler import FollowageCommandHandler


class CommandRegistry:
    def __init__(
        self,
        followage: FollowageCommandHandler,
        ask: AskCommandHandler,
        battle: BattleCommandHandler,
        roll,
        balance,
        bonus,
        transfer,
        shop,
        equipment,
        top_bottom,
        stats,
        help,
        guess,
        rps,
    ):
        self.followage: FollowageCommandHandler = followage
        self.ask: AskCommandHandler = ask
        self.battle: BattleCommandHandler = battle
        self.roll = roll
        self.balance = balance
        self.bonus = bonus
        self.transfer = transfer
        self.shop = shop
        self.equipment = equipment
        self.top_bottom = top_bottom
        self.stats = stats
        self.help = help
        self.guess = guess
        self.rps = rps
