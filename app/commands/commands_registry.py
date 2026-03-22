from app.commands.equipment.infrastructure.equipment_command_handler import EquipmentCommandHandler
from app.commands.guess.application.guess_command_handler import GuessCommandHandler
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandler
from app.commands.help.application.help_command_handler import HelpCommandHandler
from app.commands.shop.application.shop_command_handler import ShopCommandHandler
from app.commands.stats.infrastructure.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.application.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.transfer_command_handler import TransferCommandHandler


class CommandRegistry:
    def __init__(
        self,
        transfer_command_handler: TransferCommandHandler,
        shop_command_handler: ShopCommandHandler,
        equipment_command_handler: EquipmentCommandHandler,
        top_bottom_command_handler: TopBottomCommandHandler,
        stats_command_handler: StatsCommandHandler,
        help_command_handler: HelpCommandHandler,
        guess_command_handler: GuessCommandHandler,
        rps_command_handler: RpsCommandHandler,
    ):
        self.transfer_command_handler = transfer_command_handler
        self.shop_command_handler = shop_command_handler
        self.equipment_command_handler = equipment_command_handler
        self.top_bottom_command_handler = top_bottom_command_handler
        self.stats_command_handler = stats_command_handler
        self.help_command_handler = help_command_handler
        self.guess_command_handler = guess_command_handler
        self.rps_command_handler = rps_command_handler
