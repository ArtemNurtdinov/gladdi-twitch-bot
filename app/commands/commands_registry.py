from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.battle.presentation.battle_command_handler import BattleCommandHandler
from app.commands.bonus.presentation.bonus_command_handler import BonusCommandHandler
from app.commands.equipment.presentation.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.presentation.followage_command_handler import FollowageCommandHandler
from app.commands.guess.presentation.guess_command_handler import GuessCommandHandler
from app.commands.guess.presentation.rps_command_handler import RpsCommandHandler
from app.commands.help.presentation.help_command_handler import HelpCommandHandler
from app.commands.roll.presentation.roll_command_handler import RollCommandHandler
from app.commands.shop.presentation.shop_command_handler import ShopCommandHandler
from app.commands.stats.presentation.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.presentation.top_bottom_command_handler import TopBottomCommandHandler


class CommandRegistry:
    def __init__(
        self,
        followage: FollowageCommandHandler,
        ask: AskCommandHandler,
        battle: BattleCommandHandler,
        roll_command_handler: RollCommandHandler,
        balance,
        bonus: BonusCommandHandler,
        transfer,
        shop_command_handler: ShopCommandHandler,
        equipment: EquipmentCommandHandler,
        top_bottom_command_handler: TopBottomCommandHandler,
        stats_command_handler: StatsCommandHandler,
        help_command_handler: HelpCommandHandler,
        guess: GuessCommandHandler,
        rps: RpsCommandHandler,
    ):
        self.followage: FollowageCommandHandler = followage
        self.ask: AskCommandHandler = ask
        self.battle: BattleCommandHandler = battle
        self.roll_command_handler: RollCommandHandler = roll_command_handler
        self.balance = balance
        self.bonus: BonusCommandHandler = bonus
        self.transfer = transfer
        self.shop_command_handler: ShopCommandHandler = shop_command_handler
        self.equipment: EquipmentCommandHandler = equipment
        self.top_bottom_command_handler: TopBottomCommandHandler = top_bottom_command_handler
        self.stats_command_handler: StatsCommandHandler = stats_command_handler
        self.help_command_handler: HelpCommandHandler = help_command_handler
        self.guess: GuessCommandHandler = guess
        self.rps: RpsCommandHandler = rps
