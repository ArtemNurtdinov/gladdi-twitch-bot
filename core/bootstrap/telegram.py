from dataclasses import dataclass

import telegram
from telegram.request import HTTPXRequest


@dataclass
class TelegramProviders:
    telegram_bot: telegram.Bot


def build_telegram_providers(tg_bot_token: str) -> TelegramProviders:
    http_request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
    telegram_bot = telegram.Bot(token=tg_bot_token, request=http_request)
    return TelegramProviders(telegram_bot=telegram_bot)
