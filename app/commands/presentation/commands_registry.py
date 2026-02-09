from app.commands.application.commands_registry import CommandRegistryProtocol
from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.balance.presentation.balance_command_handler import BalanceCommandHandler
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
from app.commands.transfer.presentation.transfer_command_handler import TransferCommandHandler


class CommandRegistry(CommandRegistryProtocol):
    def __init__(
        self,
        followage_command_handler: FollowageCommandHandler,
        ask_command_handler: AskCommandHandler,
        battle_command_handler: BattleCommandHandler,
        roll_command_handler: RollCommandHandler,
        balance_command_handler: BalanceCommandHandler,
        bonus_command_handler: BonusCommandHandler,
        transfer_command_handler: TransferCommandHandler,
        shop_command_handler: ShopCommandHandler,
        equipment_command_handler: EquipmentCommandHandler,
        top_bottom_command_handler: TopBottomCommandHandler,
        stats_command_handler: StatsCommandHandler,
        help_command_handler: HelpCommandHandler,
        guess_command_handler: GuessCommandHandler,
        rps_command_handler: RpsCommandHandler,
    ):
        self.followage_command_handler = followage_command_handler
        self.ask_command_handler = ask_command_handler
        self.battle_command_handler = battle_command_handler
        self.roll_command_handler = roll_command_handler
        self.balance_command_handler = balance_command_handler
        self.bonus_command_handler = bonus_command_handler
        self.transfer_command_handler = transfer_command_handler
        self.shop_command_handler = shop_command_handler
        self.equipment_command_handler = equipment_command_handler
        self.top_bottom_command_handler = top_bottom_command_handler
        self.stats_command_handler = stats_command_handler
        self.help_command_handler = help_command_handler
        self.guess_command_handler = guess_command_handler
        self.rps_command_handler = rps_command_handler
