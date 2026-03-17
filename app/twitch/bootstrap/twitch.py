from app.platform.auth.platform_auth import PlatformAuth
from app.twitch.infrastructure.adapters.chatters_adapter import ChattersApiAdapter
from app.twitch.infrastructure.adapters.followage_adapter import FollowageApiAdapter
from app.twitch.infrastructure.adapters.moderation_adapter import ModerationApiAdapter
from app.twitch.infrastructure.adapters.stream_adapter import StreamApiAdapter
from app.twitch.infrastructure.adapters.user_info_adapter import UserInfoApiAdapter
from app.twitch.infrastructure.helix.client import TwitchHelixClient
from app.twitch.infrastructure.twitch_api_service import TwitchApiService


def build_twitch_api_service(auth: PlatformAuth) -> TwitchApiService:
    client = TwitchHelixClient(auth)
    user_info_adapter = UserInfoApiAdapter(client)
    followage_adapter = FollowageApiAdapter(client, user_info_adapter)
    stream_adapter = StreamApiAdapter(client, user_info_adapter)
    chatters_adapter = ChattersApiAdapter(client)
    moderation_adapter = ModerationApiAdapter(client)
    return TwitchApiService(
        client=client,
        user_info_adapter=user_info_adapter,
        followage_adapter=followage_adapter,
        stream_info_adapter=stream_adapter,
        stream_status_adapter=stream_adapter,
        chatters_adapter=chatters_adapter,
        moderation_adapter=moderation_adapter,
    )
