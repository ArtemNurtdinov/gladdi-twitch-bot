from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import ShopItems, TransactionType
from app.equipment.domain.equipment_service import EquipmentService
from app.twitch.application.interaction.shop.dto import ShopBuyDTO, ShopListDTO
from app.twitch.application.shared.chat_use_case_provider import ChatUseCaseProvider


class HandleShopUseCase:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        equipment_service_factory: Callable[[Session], EquipmentService],
        chat_use_case_provider: ChatUseCaseProvider,
    ):
        self._economy_service_factory = economy_service_factory
        self._equipment_service_factory = equipment_service_factory
        self._chat_use_case_provider = chat_use_case_provider

    async def handle_shop(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: ShopListDTO,
    ) -> str:
        all_items = ShopItems.get_all_items()
        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        result_parts = ["МАГАЗИН АРТЕФАКТОВ:"]
        for _, item in sorted_items:
            result_parts.append(f"{item.emoji} {item.name} - {item.price} монет.")

        result_parts.append(
            f"Используй: {dto.command_prefix}{dto.command_buy_name} [название предмета]. "
            f"Пример: {dto.command_prefix}{dto.command_buy_name} стул. Все предметы действуют 30 дней!"
        )
        result = "\n".join(result_parts)

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=dto.channel_name,
                user_name=dto.bot_nick,
                content=result,
                current_time=dto.occurred_at,
            )

        return result

    async def handle_buy(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: ShopBuyDTO,
    ) -> str:
        bot_nick = dto.bot_nick
        user_name = dto.user_name

        if not dto.item_name_input:
            result = (
                f"@{dto.display_name}, укажи название предмета! "
                f"Используй: {dto.command_prefix}{dto.command_buy_name} [название]. "
                f"Пример: {dto.command_prefix}{dto.command_buy_name} стул"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, result, dto.occurred_at)
            return result

        try:
            item_type = ShopItems.find_item_by_name(dto.item_name_input)
        except ValueError as e:
            result = str(e)
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, result, dto.occurred_at)
            return result

        item = ShopItems.get_item(item_type)

        with db_readonly_session_provider() as db:
            equipment_exists = self._equipment_service_factory(db).equipment_exists(dto.channel_name, user_name, item_type)

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, result, dto.occurred_at)
            return result

        with db_session_provider() as db:
            user_balance = self._economy_service_factory(db).get_user_balance(dto.channel_name, user_name)

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, result, dto.occurred_at)
            return result

        with db_session_provider() as db:
            self._economy_service_factory(db).subtract_balance(
                channel_name=dto.channel_name,
                user_name=user_name,
                amount=item.price,
                transaction_type=TransactionType.SHOP_PURCHASE,
                description=f"Покупка '{item.name}'",
            )
            self._equipment_service_factory(db).add_equipment_to_user(dto.channel_name, user_name, item_type)

        result = f"@{dto.display_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(dto.channel_name, bot_nick, result, dto.occurred_at)
        return result

