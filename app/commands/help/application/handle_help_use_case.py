from app.commands.help.application.help_uow import HelpUnitOfWorkFactory
from app.commands.help.application.model import HelpDTO


class HandleHelpUseCase:
    def __init__(self, unit_of_work_factory: HelpUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(
        self,
        command_help: HelpDTO,
    ) -> str:
        user_message = command_help.command_prefix + command_help.command_name
        help_parts = ["📜 Доступные команды:"]
        for cmd in command_help.commands:
            help_parts.append(f"{command_help.command_prefix}{cmd}")
        help_text = " ".join(help_parts)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=command_help.channel_name,
                user_name=command_help.user_name,
                content=user_message,
                current_time=command_help.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=command_help.channel_name,
                user_name=command_help.bot_nick,
                content=help_text,
                current_time=command_help.occurred_at,
            )

        return help_text
