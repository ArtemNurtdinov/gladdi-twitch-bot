from datetime import datetime

from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.application.model import CommandShopDTO
from app.platform.command.domain.command_handler import CommandHandler


class ShopCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
        bot_nick: str,
    ):
        self.command_prefix = command_prefix
        self.command_shop_name = command_shop_name
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_nick = bot_nick

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        bot_nick = self._bot_nick.lower()

        command_shop = CommandShopDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            command_prefix=self.command_prefix,
            command_name=self.command_shop_name,
            command_buy_name=self.command_buy_name,
        )

        return await self._handle_shop_use_case.handle_shop(command_shop=command_shop)
