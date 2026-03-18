from app.commands.balance.application.balance_uow import BalanceUnitOfWorkFactory
from app.commands.balance.application.model import BalanceDTO


class HandleBalanceUseCase:
    def __init__(self, balance_uow: BalanceUnitOfWorkFactory):
        self._balance_uow = balance_uow

    async def handle(self, command_balance: BalanceDTO) -> str:
        user_message = command_balance.command_prefix + command_balance.command_name

        with self._balance_uow.create(read_only=True) as uow:
            user_balance = uow.economy_policy.get_user_balance(
                channel_name=command_balance.channel_name,
                user_name=command_balance.user_name,
            )

        result = f"💰 @{command_balance.display_name}, твой баланс: {user_balance.balance} монет"

        with self._balance_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_balance.channel_name,
                user_name=command_balance.user_name,
                content=user_message,
                current_time=command_balance.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_balance.channel_name,
                user_name=command_balance.bot_nick,
                content=result,
                current_time=command_balance.occurred_at,
            )

        return result
