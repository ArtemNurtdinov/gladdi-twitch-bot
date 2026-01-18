from app.commands.transfer.application.model import TransferDTO
from app.commands.transfer.application.transfer_uow import TransferUnitOfWorkFactory


class HandleTransferUseCase:
    def __init__(self, unit_of_work_factory: TransferUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(
        self,
        command_transfer: TransferDTO,
    ) -> str:
        command_prefix = command_transfer.command_prefix
        command_name = command_transfer.channel_name
        user_message = command_transfer.command_prefix + command_transfer.command_name
        if command_transfer.recipient_input:
            user_message += command_transfer.recipient_input
        if command_transfer.amount_input:
            user_message += command_transfer.amount_input

        if not command_transfer.recipient_input or not command_transfer.amount_input:
            result = (
                f"@{command_transfer.display_name}, используй: {command_prefix}{command_name} [никнейм] [сумма]. "
                f"Например: {command_transfer.command_prefix}{command_transfer.command_name} @ArtemNeFRiT 100"
            )
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.user_name,
                    content=user_message,
                    current_time=command_transfer.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at,
                )
            return result

        try:
            transfer_amount = int(command_transfer.amount_input)
        except ValueError:
            result = (
                f"@{command_transfer.display_name}, неверная сумма! Укажи число. "
                f"Например: {command_transfer.command_prefix}{command_transfer.command_name} {command_transfer.recipient_input} 100"
            )
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.user_name,
                    content=user_message,
                    current_time=command_transfer.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at,
                )
            return result

        if transfer_amount <= 0:
            result = f"@{command_transfer.display_name}, сумма должна быть больше 0!"
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.user_name,
                    content=user_message,
                    current_time=command_transfer.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at,
                )
            return result

        recipient = command_transfer.recipient_input.lstrip("@")
        normalized_receiver_name = recipient.lower()

        with self._unit_of_work_factory.create() as uow:
            transfer_result = uow.economy_policy.transfer_money(
                channel_name=command_transfer.channel_name,
                sender_name=command_transfer.user_name,
                receiver_name=normalized_receiver_name,
                amount=transfer_amount,
            )

        if transfer_result.success:
            result = f"@{command_transfer.display_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{command_transfer.display_name}, {transfer_result.message}"

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_transfer.channel_name,
                user_name=command_transfer.user_name,
                content=user_message,
                current_time=command_transfer.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_transfer.channel_name,
                user_name=command_transfer.bot_nick,
                content=result,
                current_time=command_transfer.occurred_at,
            )

        return result
