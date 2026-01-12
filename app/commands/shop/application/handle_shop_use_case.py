from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.shop.application.model import CommandBuyDTO, CommandShopDTO
from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.domain.models import ShopItems, TransactionType
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from core.provider import Provider


class HandleShopUseCase:
    def __init__(
        self,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case_provider: Provider[AddEquipmentUseCase],
        equipment_exists_use_case_provider: Provider[EquipmentExistsUseCase],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        self._economy_policy_provider = economy_policy_provider
        self._add_equipment_use_case_provider = add_equipment_use_case_provider
        self._equipment_exists_use_case_provider = equipment_exists_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_shop(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_shop: CommandShopDTO,
    ) -> str:
        all_items = ShopItems.get_all_items()
        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        user_message = command_shop.command_prefix + command_shop.command_name

        result_parts = ["МАГАЗИН АРТЕФАКТОВ:"]
        for _, item in sorted_items:
            result_parts.append(f"{item.emoji} {item.name} - {item.price} монет.")

        result_parts.append(
            f"Используй: {command_shop.command_prefix}{command_shop.command_buy_name} [название предмета]. "
            f"Пример: {command_shop.command_prefix}{command_shop.command_buy_name} стул. Все предметы действуют 30 дней!"
        )
        result = "\n".join(result_parts)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_shop.channel_name,
                user_name=command_shop.user_name,
                content=user_message,
                current_time=command_shop.occurred_at,
            )
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_shop.channel_name,
                user_name=command_shop.bot_nick,
                content=result,
                current_time=command_shop.occurred_at,
            )
        return result

    async def handle_buy(
        self,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
        command_buy: CommandBuyDTO,
    ) -> str:
        user_name = command_buy.user_name

        user_message = command_buy.command_prefix + command_buy.command_name

        if not command_buy.item_name_input:
            result = (
                f"@{command_buy.display_name}, укажи название предмета! "
                f"Используй: {command_buy.command_prefix}{command_buy.command_name} [название]. "
                f"Пример: {command_buy.command_prefix}{command_buy.command_name} стул"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        try:
            item_type = ShopItems.find_item_by_name(command_buy.item_name_input)
        except ValueError as e:
            result = str(e)
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        item = ShopItems.get_item(item_type)

        with db_readonly_session_provider() as db:
            equipment_exists = self._equipment_exists_use_case_provider.get(db).check_equipment_exists(
                channel_name=command_buy.channel_name, user_name=user_name, item_type=item_type
            )

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        with db_session_provider() as db:
            user_balance = self._economy_policy_provider.get(db).get_user_balance(
                channel_name=command_buy.channel_name, user_name=user_name
            )

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        with db_session_provider() as db:
            self._economy_policy_provider.get(db).subtract_balance(
                channel_name=command_buy.channel_name,
                user_name=user_name,
                amount=item.price,
                transaction_type=TransactionType.SHOP_PURCHASE,
                description=f"Покупка '{item.name}'",
            )
            self._add_equipment_use_case_provider.get(db).add(
                channel_name=command_buy.channel_name, user_name=user_name, item_type=item_type
            )

        result = f"@{command_buy.display_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_buy.channel_name,
                user_name=command_buy.user_name,
                content=user_message,
                current_time=command_buy.occurred_at,
            )
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_buy.channel_name, user_name=command_buy.bot_nick, content=result, current_time=command_buy.occurred_at
            )
        return result
