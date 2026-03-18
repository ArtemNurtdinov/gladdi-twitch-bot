from typing import Protocol

from app.commands.ask.application.ask_command_handler import AskCommandHandler
from app.commands.balance.application.balance_command_handler import BalanceCommandHandler
from app.commands.battle.application.battle_command_handler import BattleCommandHandler
from app.commands.bonus.application.bonus_command_handler import BonusCommandHandler
from app.commands.equipment.application.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.application.followage_command_handler import FollowageCommandHandler
from app.commands.guess.application.guess_command_handler import GuessCommandHandler
from app.commands.guess.application.rps_command_handler import RpsCommandHandler
from app.commands.help.application.help_command_handler import HelpCommandHandler
from app.commands.roll.application.roll_command_handler import RollCommandHandler
from app.commands.shop.application.shop_command_handler import ShopCommandHandler
from app.commands.stats.application.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.application.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.transfer_command_handler import TransferCommandHandler


class CommandRegistryProtocol(Protocol):
    followage_command_handler: FollowageCommandHandler
    ask_command_handler: AskCommandHandler
    battle_command_handler: BattleCommandHandler
    roll_command_handler: RollCommandHandler
    balance_command_handler: BalanceCommandHandler
    bonus_command_handler: BonusCommandHandler
    transfer_command_handler: TransferCommandHandler
    shop_command_handler: ShopCommandHandler
    equipment_command_handler: EquipmentCommandHandler
    top_bottom_command_handler: TopBottomCommandHandler
    stats_command_handler: StatsCommandHandler
    help_command_handler: HelpCommandHandler
    guess_command_handler: GuessCommandHandler
    rps_command_handler: RpsCommandHandler
