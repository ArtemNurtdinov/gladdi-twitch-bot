import logging

from app.platform.auth.platform_auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.twitch.infrastructure.chat.twitch_chat_client import TwitchChatClient
from app.twitch.infrastructure.helix.auth import TwitchAuth
from core.chat.outbound import ChatOutbound


def _validate_credentials(access_token: str, refresh_token: str, client_id: str, client_secret: str) -> None:
    missing = []
    if not client_id:
        missing.append("client_id")
    if not client_secret:
        missing.append("client_secret")
    if not refresh_token:
        missing.append("refresh_token")
    if not access_token:
        missing.append("access_token")

    if missing:
        raise ValueError(f"Недостаточно данных для авторизации платформы: {', '.join(missing)}")


def twitch_auth_factory(
    access_token: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> TwitchAuth:
    _validate_credentials(access_token, refresh_token, client_id, client_secret)
    return TwitchAuth(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        logger=logging.getLogger(__name__),
    )


def twitch_chat_client_factory(auth: PlatformAuth, settings: BotSettings, bot_id: str) -> ChatOutbound:
    return TwitchChatClient(auth=auth, settings=settings, bot_id=bot_id)
