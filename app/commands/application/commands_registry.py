from collections.abc import Awaitable
from typing import Protocol

from app.commands.ask.application.ask_command_handler import AskCommandHandler
from app.commands.balance.application.balance_command_handler import BalanceCommandHandler
from app.commands.battle.application.battle_command_handler import BattleCommandHandler
from app.commands.bonus.application.bonus_command_handler import BonusCommandHandler
from app.commands.domain.interfaces import ChatContext
from app.commands.equipment.application.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.application.followage_command_handler import FollowageCommandHandler
from app.commands.roll.application.roll_command_handler import RollCommandHandler
from app.commands.shop.application.shop_command_handler import ShopCommandHandler
from app.commands.top_bottom.application.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.transfer_command_handler import TransferCommandHandler


class SimpleCommandHandler(Protocol):
    def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...


class GuessCommandHandler(Protocol):
    def handle_guess_number(self, channel_name: str, display_name: str, chat_ctx: ChatContext, number: str | None) -> Awaitable[None]: ...
    def handle_guess_letter(self, channel_name: str, display_name: str, chat_ctx: ChatContext, letter: str | None) -> Awaitable[None]: ...
    def handle_guess_word(self, channel_name: str, display_name: str, chat_ctx: ChatContext, word: str | None) -> Awaitable[None]: ...


class RpsCommandHandler(Protocol):
    def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext, choice: str | None) -> Awaitable[None]: ...


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
    stats_command_handler: SimpleCommandHandler
    help_command_handler: SimpleCommandHandler
    guess_command_handler: GuessCommandHandler
    rps_command_handler: RpsCommandHandler
