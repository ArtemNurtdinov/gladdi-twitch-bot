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
    ):
        self.command_prefix = command_prefix
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_nick = bot_nick

    async def handle(self, channel_name: str, user_name: str, message: str) -> str | None:
        tail = message[len(self.command_prefix + self.command_buy_name) :].strip()
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

        return await self._handle_shop_use_case.handle_buy(command_buy=command_buy)
