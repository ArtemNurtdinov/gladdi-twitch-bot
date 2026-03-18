from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.application.commands_registry import ShopCommandHandler
from app.commands.domain.interfaces import ChatContext
from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.application.model import CommandBuyDTO, CommandShopDTO


class ShopCommandHandlerImpl(ShopCommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
        bot_nick: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_shop_name = command_shop_name
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle_shop(self, channel_name: str, display_name: str, chat_ctx: ChatContext):
        bot_nick = self._bot_nick.lower()

        command_shop = CommandShopDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            command_prefix=self.command_prefix,
            command_name=self.command_shop_name,
            command_buy_name=self.command_buy_name,
        )

        result = await self._handle_shop_use_case.handle_shop(command_shop=command_shop)

        await self.post_message_fn(result)

    async def handle_buy(self, channel_name: str, display_name: str, chat_ctx: ChatContext, item_name: str | None):
        bot_name = self._bot_nick.lower()

        command_buy = CommandBuyDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_buy_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_name,
            occurred_at=datetime.utcnow(),
            item_name_input=item_name,
        )

        result = await self._handle_shop_use_case.handle_buy(command_buy=command_buy)

        await self.post_message_fn(result)
