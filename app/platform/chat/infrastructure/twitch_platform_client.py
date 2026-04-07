from app.core.logger.domain.logger import Logger
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.application.platform_chat_client import PlatformChatClient
from app.platform.chat.application.usecase.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.usecase.handle_reply_use_case import HandleReplyUseCase
from app.platform.chat.infrastructure.twitch_chat_client import TwitchChatClient
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter


class TwitchPlatformChatClient(PlatformChatClient):
    def __init__(
        self,
        handle_chat_message_use_case: HandleChatMessageUseCase,
        handle_reply_use_case: HandleReplyUseCase,
        command_router: CommandRouter,
        command_prefix: str,
        help_command_handler: CommandHandler,
        logger: Logger,
    ):
        PlatformChatClient.__init__(
            self,
            handle_chat_message_use_case=handle_chat_message_use_case,
            handle_reply_use_case=handle_reply_use_case,
            command_router=command_router,
            command_prefix=command_prefix,
            help_command_handler=help_command_handler,
            logger=logger,
        )
        self._twitch_client: TwitchChatClient | None = None

    def init_client(self, auth: PlatformAuth, channel_name: str, bot_name: str, bot_id: str):
        super().init(channel_name, bot_name)
        self._twitch_client = TwitchChatClient(auth, bot_id, self.logger, self.handle_message, channel_name)

    def is_reply_message(self, message: str) -> bool:
        return message.lower().startswith(f"@{self.bot_name}")

    async def send_channel_message(self, message: str):
        await self._twitch_client.send_channel_message(message)

    async def start_chat(self):
        await self._twitch_client.start_chat()

    async def stop_chat(self):
        await self._twitch_client.stop_chat()
