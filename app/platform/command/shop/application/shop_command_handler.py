from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.shop.application.handle_shop_use_case import HandleShopUseCase
from app.platform.command.shop.application.model import CommandShopDTO


class ShopCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
    ):
        self.command_prefix = command_prefix
        self.command_shop_name = command_shop_name
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        command_shop = CommandShopDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            command_prefix=self.command_prefix,
            command_name=self.command_shop_name,
            command_buy_name=self.command_buy_name,
            message=message,
        )

        return await self._handle_shop_use_case.handle_shop(command_shop=command_shop)
