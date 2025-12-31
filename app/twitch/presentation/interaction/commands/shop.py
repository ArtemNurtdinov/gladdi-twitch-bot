from datetime import datetime
from typing import Any, Awaitable, Callable, ContextManager

from sqlalchemy.orm import Session

from app.commands.shop.model import CommandBuyDTO, CommandShopDTO
from app.commands.shop.handle_shop_use_case import HandleShopUseCase


class ShopCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_shop_name: str,
        command_buy_name: str,
        handle_shop_use_case: HandleShopUseCase,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_shop_name = command_shop_name
        self.command_buy_name = command_buy_name
        self._handle_shop_use_case = handle_shop_use_case
        self._db_session_provider = db_session_provider
        self._db_readonly_session_provider = db_readonly_session_provider
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle_shop(self, channel_name: str, display_name: str, ctx):
        bot_nick = self.bot_nick_provider().lower()

        dto = CommandShopDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            command_prefix=self.command_prefix,
            command_name=self.command_shop_name,
            command_buy_name=self.command_buy_name,
        )

        result = await self._handle_shop_use_case.handle_shop(
            db_session_provider=self._db_session_provider,
            command_shop=dto,
        )

        await self.post_message_fn(result, ctx)

    async def handle_buy(self, channel_name: str, display_name: str, ctx, item_name: str | None):
        bot_nick = self.bot_nick_provider().lower()

        dto = CommandBuyDTO(
            command_prefix=self.command_prefix,
            command_name=self.command_buy_name,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
            item_name_input=item_name,
        )

        result = await self._handle_shop_use_case.handle_buy(
            db_session_provider=self._db_session_provider,
            db_readonly_session_provider=self._db_readonly_session_provider,
            command_buy=dto,
        )

        await self.post_message_fn(result, ctx)
