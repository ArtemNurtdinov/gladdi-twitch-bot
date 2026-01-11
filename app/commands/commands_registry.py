from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.battle.presentation.battle_command_handler import BattleCommandHandler
from app.commands.bonus.presentation.bonus_command_handler import BonusCommandHandler
from app.commands.equipment.presentation.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.presentation.followage_command_handler import FollowageCommandHandler
from app.commands.guess.presentation.guess_command_handler import GuessCommandHandler
from app.commands.guess.presentation.rps_command_handler import RpsCommandHandler


class CommandRegistry:
    def __init__(
        self,
        followage: FollowageCommandHandler,
        ask: AskCommandHandler,
        battle: BattleCommandHandler,
        roll,
        balance,
        bonus: BonusCommandHandler,
        transfer,
        shop,
        equipment: EquipmentCommandHandler,
        top_bottom,
        stats,
        help,
        guess: GuessCommandHandler,
        rps: RpsCommandHandler,
    ):
        self.followage: FollowageCommandHandler = followage
        self.ask: AskCommandHandler = ask
        self.battle: BattleCommandHandler = battle
        self.roll = roll
        self.balance = balance
        self.bonus: BonusCommandHandler = bonus
        self.transfer = transfer
        self.shop = shop
        self.equipment: EquipmentCommandHandler = equipment
        self.top_bottom = top_bottom
        self.stats = stats
        self.help = help
        self.guess: GuessCommandHandler = guess
        self.rps: RpsCommandHandler = rps
