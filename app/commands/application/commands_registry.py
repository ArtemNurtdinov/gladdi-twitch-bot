from collections.abc import Awaitable, MutableMapping
from typing import Protocol

from core.chat.interfaces import ChatContext


class SimpleCommandHandler(Protocol):
    def handle(self, channel_name: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...


class AskCommandHandler(Protocol):
    def handle(self, channel_name: str, full_message: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...


class FollowageCommandHandler(Protocol):
    def handle(self, channel_name: str, display_name: str, author_id: str, chat_ctx: ChatContext) -> Awaitable[None]: ...


class BattleCommandHandler(Protocol):
    def handle(
        self,
        channel_name: str,
        display_name: str,
        battle_waiting_user_ref: MutableMapping[str, str | None],
        chat_ctx: ChatContext,
    ) -> Awaitable[None]: ...


class RollCommandHandler(Protocol):
    def handle(self, chat_ctx: ChatContext, channel_name: str, display_name: str, amount: str | None = None) -> Awaitable[None]: ...


class TransferCommandHandler(Protocol):
    def handle(
        self,
        channel_name: str,
        sender_display_name: str,
        chat_ctx: ChatContext,
        recipient: str | None = None,
        amount: str | None = None,
    ) -> Awaitable[None]: ...


class ShopCommandHandler(Protocol):
    def handle_shop(self, channel_name: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...
    def handle_buy(self, channel_name: str, display_name: str, chat_ctx: ChatContext, item_name: str | None) -> Awaitable[None]: ...


class TopBottomCommandHandler(Protocol):
    def handle_top(self, channel_name: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...
    def handle_bottom(self, channel_name: str, display_name: str, chat_ctx: ChatContext) -> Awaitable[None]: ...


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
    balance_command_handler: SimpleCommandHandler
    bonus_command_handler: SimpleCommandHandler
    transfer_command_handler: TransferCommandHandler
    shop_command_handler: ShopCommandHandler
    equipment_command_handler: SimpleCommandHandler
    top_bottom_command_handler: TopBottomCommandHandler
    stats_command_handler: SimpleCommandHandler
    help_command_handler: SimpleCommandHandler
    guess_command_handler: GuessCommandHandler
    rps_command_handler: RpsCommandHandler
