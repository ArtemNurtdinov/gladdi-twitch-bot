from app.platform.auth import PlatformAuth
from app.platform.providers import PlatformProviders
from app.twitch.infrastructure.adapters.twitch_platform_adapter import TwitchStreamingPlatformAdapter
from app.twitch.infrastructure.auth import TwitchAuth
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


def build_twitch_providers(platform_auth: PlatformAuth) -> PlatformProviders:
    twitch_auth: TwitchAuth = platform_auth  # type: ignore[assignment]
    twitch_api_service = TwitchApiService(twitch_auth)
    streaming_platform = TwitchStreamingPlatformAdapter(twitch_api_service)
    return PlatformProviders(
        platform_auth=platform_auth,
        streaming_platform=streaming_platform,
        api_client=twitch_api_service,
    )
