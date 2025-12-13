from abc import ABC, abstractmethod
from typing import Optional, List
from features.twitch.api.model.stream_info import StreamInfo
from features.twitch.api.model.user_info import UserInfo
from features.twitch.api.model.follow_info import FollowInfo
from features.twitch.api.model.stream_status import StreamStatus
from features.twitch.api.model.channel_info import ChannelInfo


class ITwitchApiService(ABC):
    
    @abstractmethod
    async def get_user_by_login(self, login: str) -> Optional[UserInfo]:
        pass
    
    @abstractmethod
    async def get_user_followage(self, broadcaster_id: str, user_id: str) -> Optional[FollowInfo]:
        pass
    
    @abstractmethod
    async def get_stream_info(self, broadcaster_id: str) -> StreamInfo:
        pass
    
    @abstractmethod
    async def get_stream_status(self, broadcaster_id: str) -> Optional[StreamStatus]:
        pass
    
    @abstractmethod
    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        pass
    
    @abstractmethod
    async def get_channel_info(self, broadcaster_id: str) -> ChannelInfo:
        pass
    
    @abstractmethod
    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> List[str]:
        pass