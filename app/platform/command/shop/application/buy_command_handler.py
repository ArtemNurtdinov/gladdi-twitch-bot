from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.shop.application.handle_shop_use_case import HandleShopUseCase
from app.platform.command.shop.application.model import CommandBuyDTO


class BuyCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
    ):
        self.command_prefix = command_prefix
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        tail = message[len(self.command_prefix + self.command_buy_name) :].strip()
        item_name = tail or None

        command_buy = CommandBuyDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_buy_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            item_name_input=item_name,
            message=message,
        )

        return await self._handle_shop_use_case.handle_buy(command_buy=command_buy)
