import asyncio
import logging
from datetime import datetime
from typing import Callable

from core.db import SessionLocal, db_ro_session
from app.economy.domain.models import TransactionType
from app.economy.domain.models import ShopItems

logger = logging.getLogger(__name__)


class ShopCommandHandler:

    def __init__(
        self,
        economy_service_factory,
        equipment_service_factory,
        chat_use_case_factory,
        command_shop: str,
        command_buy: str,
        prefix: str,
        nick_provider: Callable[[], str],
        split_text_fn: Callable[[str], list[str]],
    ):
        self._economy_service = economy_service_factory
        self._equipment_service = equipment_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_shop = command_shop
        self.command_buy = command_buy
        self.prefix = prefix
        self.nick_provider = nick_provider
        self.split_text = split_text_fn

    async def handle_shop(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_shop} от пользователя {user_name}")

        all_items = ShopItems.get_all_items()

        result = "МАГАЗИН АРТЕФАКТОВ:\n"

        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        for item_type, item in sorted_items:
            result += f"{item.emoji} {item.name} - {item.price} монет. "

        result += (
            f"Используй: {self.prefix}{self.command_buy} [название предмета]. "
            f"Пример: {self.prefix}{self.command_buy} стул. Все предметы действуют 30 дней!"
        )

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def handle_buy(self, ctx, item_name: str | None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда {self.command_buy} от пользователя {user_name}")

        if not item_name:
            result = (
                f"@{user_name}, укажи название предмета! Используй: {self.prefix}{self.command_buy} [название]. "
                f"Пример: {self.prefix}{self.command_buy} стул"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            item_type = ShopItems.find_item_by_name(item_name)
        except ValueError as e:
            result = str(e)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        item = ShopItems.get_item(item_type)

        normalized_user_name = user_name.lower()
        with db_ro_session() as db:
            equipment_exists = self._equipment_service(db).equipment_exists(channel_name, normalized_user_name, item_type)

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, normalized_user_name)

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            self._economy_service(db).subtract_balance(
                channel_name, normalized_user_name, item.price, TransactionType.SHOP_PURCHASE, f"Покупка '{item.name}'"
            )
            self._equipment_service(db).add_equipment_to_user(channel_name, normalized_user_name, item_type)

        result = f"@{user_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

