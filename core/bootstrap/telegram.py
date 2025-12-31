from dataclasses import dataclass

import telegram
from telegram.request import HTTPXRequest

from core.config import config


@dataclass
class TelegramProviders:
    telegram_bot: telegram.Bot


def build_telegram_providers() -> TelegramProviders:
    http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
    telegram_bot = telegram.Bot(token=config.telegram.bot_token, request=http_request)
    return TelegramProviders(telegram_bot=telegram_bot)
