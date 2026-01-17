from app.commands.balance.application.balance_uow import BalanceUnitOfWorkFactory
from app.commands.balance.application.model import BalanceDTO


class HandleBalanceUseCase:
    def __init__(
        self,
        unit_of_work_factory: BalanceUnitOfWorkFactory,
    ):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(
        self,
        command_balance_dto: BalanceDTO,
    ) -> str:
        user_message = command_balance_dto.command_prefix + command_balance_dto.command_name

        with self._unit_of_work_factory.create(read_only=True) as uow:
            user_balance = uow.economy_policy.get_user_balance(
                channel_name=command_balance_dto.channel_name,
                user_name=command_balance_dto.user_name,
            )

        result = f"💰 @{command_balance_dto.display_name}, твой баланс: {user_balance.balance} монет"

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_balance_dto.channel_name,
                user_name=command_balance_dto.user_name,
                content=user_message,
                current_time=command_balance_dto.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_balance_dto.channel_name,
                user_name=command_balance_dto.bot_nick,
                content=result,
                current_time=command_balance_dto.occurred_at,
            )

        return result
