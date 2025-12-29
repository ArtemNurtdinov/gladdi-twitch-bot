from typing import Optional, Protocol

from app.twitch.application.common.model import StreamStatusDTO


class StreamStatusProvider(Protocol):
    async def get_stream_status(self, broadcaster_id: str) -> Optional[StreamStatusDTO]:
        ...

