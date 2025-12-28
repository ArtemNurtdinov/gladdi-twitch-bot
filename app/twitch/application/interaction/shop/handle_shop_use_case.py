from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.economy.application.economy_service_provider import EconomyServiceProvider
from app.economy.domain.models import ShopItems, TransactionType
from app.equipment.application.equipment_service_provider import EquipmentServiceProvider
from app.twitch.application.interaction.shop.dto import CommandBuyDTO, CommandShopDTO


class HandleShopUseCase:

    def __init__(
        self,
        economy_service_provider: EconomyServiceProvider,
        equipment_service_provider: EquipmentServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
    ):
        self._economy_service_provider = economy_service_provider
        self._equipment_service_provider = equipment_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_shop(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        command_shop_dto: CommandShopDTO,
    ) -> str:
        all_items = ShopItems.get_all_items()
        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        result_parts = ["МАГАЗИН АРТЕФАКТОВ:"]
        for _, item in sorted_items:
            result_parts.append(f"{item.emoji} {item.name} - {item.price} монет.")

        result_parts.append(
            f"Используй: {command_shop_dto.command_prefix}{command_shop_dto.command_buy_name} [название предмета]. "
            f"Пример: {command_shop_dto.command_prefix}{command_shop_dto.command_buy_name} стул. Все предметы действуют 30 дней!"
        )
        result = "\n".join(result_parts)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_shop_dto.channel_name,
                user_name=command_shop_dto.bot_nick,
                content=result,
                current_time=command_shop_dto.occurred_at,
            )
        return result

    async def handle_buy(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        command_buy_dto: CommandBuyDTO,
    ) -> str:
        user_name = command_buy_dto.user_name

        if not command_buy_dto.item_name_input:
            result = (
                f"@{command_buy_dto.display_name}, укажи название предмета! "
                f"Используй: {command_buy_dto.command_prefix}{command_buy_dto.command_name} [название]. "
                f"Пример: {command_buy_dto.command_prefix}{command_buy_dto.command_name} стул"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy_dto.channel_name,
                    user_name=command_buy_dto.bot_nick,
                    content=result,
                    current_time=command_buy_dto.occurred_at
                )
            return result

        try:
            item_type = ShopItems.find_item_by_name(command_buy_dto.item_name_input)
        except ValueError as e:
            result = str(e)
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy_dto.channel_name,
                    user_name=command_buy_dto.bot_nick,
                    content=result,
                    current_time=command_buy_dto.occurred_at
                )
            return result

        item = ShopItems.get_item(item_type)

        with db_readonly_session_provider() as db:
            equipment_exists = self._equipment_service_provider.get(db).equipment_exists(
                channel_name=command_buy_dto.channel_name,
                user_name=user_name,
                item_type=item_type
            )

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy_dto.channel_name,
                    user_name=command_buy_dto.bot_nick,
                    content=result,
                    current_time=command_buy_dto.occurred_at
                )
            return result

        with db_session_provider() as db:
            user_balance = self._economy_service_provider.get(db).get_user_balance(
                channel_name=command_buy_dto.channel_name,
                user_name=user_name
            )

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_buy_dto.channel_name,
                    user_name=command_buy_dto.bot_nick,
                    content=result,
                    current_time=command_buy_dto.occurred_at
                )
            return result

        with db_session_provider() as db:
            self._economy_service_provider.get(db).subtract_balance(
                channel_name=command_buy_dto.channel_name,
                user_name=user_name,
                amount=item.price,
                transaction_type=TransactionType.SHOP_PURCHASE,
                description=f"Покупка '{item.name}'",
            )
            self._equipment_service_provider.get(db).add_equipment_to_user(
                channel_name=command_buy_dto.channel_name,
                user_name=user_name,
                item_type=item_type
            )

        result = f"@{command_buy_dto.display_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_buy_dto.channel_name,
                user_name=command_buy_dto.bot_nick,
                content=result,
                current_time=command_buy_dto.occurred_at
            )
        return result
