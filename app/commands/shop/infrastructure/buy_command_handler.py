from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.application.model import CommandBuyDTO
from app.platform.command.domain.command_handler import CommandHandler


class BuyCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
        bot_nick: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self.command_prefix + self.command_buy_name) :].strip()
        item_name = tail or None

        bot_name = self._bot_nick.lower()

        command_buy = CommandBuyDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_buy_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=bot_name,
            occurred_at=datetime.utcnow(),
            item_name_input=item_name,
        )

        result = await self._handle_shop_use_case.handle_buy(command_buy=command_buy)

        await self.post_message_fn(result)
