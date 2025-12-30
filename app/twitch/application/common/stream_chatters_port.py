from typing import List, Protocol


class StreamChattersPort(Protocol):

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> List[str]:
        ...

