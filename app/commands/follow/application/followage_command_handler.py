from abc import ABC, abstractmethod


class FollowageCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str, author_id: str): ...
