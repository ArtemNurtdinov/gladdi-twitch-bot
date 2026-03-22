from app.commands.balance.application.balance_command_handler import BalanceCommandHandler
from app.commands.battle.application.battle_command_handler import BattleCommandHandler
from app.commands.bonus.application.bonus_command_handler import BonusCommandHandler
from app.commands.equipment.infrastructure.equipment_command_handler import EquipmentCommandHandler
from app.commands.guess.application.guess_command_handler import GuessCommandHandler
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandler
from app.commands.help.application.help_command_handler import HelpCommandHandler
from app.commands.roll.application.roll_command_handler import RollCommandHandler
from app.commands.shop.application.shop_command_handler import ShopCommandHandler
from app.commands.stats.infrastructure.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.application.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.transfer_command_handler import TransferCommandHandler


class CommandRegistry:
    def __init__(
        self,
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
