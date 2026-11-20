from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str | None
    group_id: int | None
    proxy_url: str | None = None
