from app.commands.shop.application.model import CommandBuyDTO, CommandShopDTO
from app.commands.shop.application.shop_uow import ShopUnitOfWorkFactory
from app.economy.domain.models import TransactionType
from app.shop.domain.models import ShopItems


class HandleShopUseCase:
    def __init__(
        self,
        unit_of_work_factory: ShopUnitOfWorkFactory,
    ):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle_shop(
        self,
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

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_shop.channel_name,
                user_name=command_shop.user_name,
                content=user_message,
                current_time=command_shop.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_shop.channel_name,
                user_name=command_shop.bot_nick,
                content=result,
                current_time=command_shop.occurred_at,
            )
        return result

    async def handle_buy(
        self,
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
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
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
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        item = ShopItems.get_item(item_type)

        with self._unit_of_work_factory.create(read_only=True) as uow:
            equipment_exists = uow.equipment_exists_use_case.check_equipment_exists(
                channel_name=command_buy.channel_name, user_name=user_name, item_type=item_type
            )

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        with self._unit_of_work_factory.create(read_only=True) as uow:
            user_balance = uow.economy_policy.get_user_balance(
                channel_name=command_buy.channel_name, user_name=user_name
            )

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.user_name,
                    content=user_message,
                    current_time=command_buy.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_buy.channel_name,
                    user_name=command_buy.bot_nick,
                    content=result,
                    current_time=command_buy.occurred_at,
                )
            return result

        with self._unit_of_work_factory.create() as uow:
            uow.economy_policy.subtract_balance(
                channel_name=command_buy.channel_name,
                user_name=user_name,
                amount=item.price,
                transaction_type=TransactionType.SHOP_PURCHASE,
                description=f"Покупка '{item.name}'",
            )
            uow.add_equipment_use_case.add(
                channel_name=command_buy.channel_name, user_name=user_name, item_type=item_type
            )

        result = f"@{command_buy.display_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_buy.channel_name,
                user_name=command_buy.user_name,
                content=user_message,
                current_time=command_buy.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_buy.channel_name, user_name=command_buy.bot_nick, content=result, current_time=command_buy.occurred_at
            )
        return result
