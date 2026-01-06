from dataclasses import dataclass

from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.infrastructure.twitch_platform_adapter import TwitchStreamingPlatformAdapter


@dataclass
class TwitchProviders:
    twitch_auth: TwitchAuth
    twitch_api_service: TwitchApiService
    streaming_platform: TwitchStreamingPlatformAdapter


def build_twitch_providers(twitch_auth: TwitchAuth) -> TwitchProviders:
    twitch_api_service = TwitchApiService(twitch_auth)
    streaming_platform = TwitchStreamingPlatformAdapter(twitch_api_service)
    return TwitchProviders(
        twitch_auth=twitch_auth,
        twitch_api_service=twitch_api_service,
        streaming_platform=streaming_platform,
    )
