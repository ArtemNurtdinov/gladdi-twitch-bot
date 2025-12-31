from dataclasses import dataclass

from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


@dataclass
class TwitchProviders:
    twitch_auth: TwitchAuth
    twitch_api_service: TwitchApiService


def build_twitch_providers(twitch_auth: TwitchAuth) -> TwitchProviders:
    twitch_api_service = TwitchApiService(twitch_auth)
    return TwitchProviders(
        twitch_auth=twitch_auth,
        twitch_api_service=twitch_api_service,
    )
