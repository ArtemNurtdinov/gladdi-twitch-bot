from dataclasses import dataclass
from app.platform.bot.bot import Bot
from core.chat.outbound import ChatOutbound
from app.platform.providers import PlatformProviders


@dataclass
class BotComposition:
    bot: Bot
    chat_client: ChatOutbound
    platform_providers: PlatformProviders
