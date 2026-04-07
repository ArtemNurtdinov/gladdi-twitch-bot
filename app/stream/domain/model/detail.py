from dataclasses import dataclass

from app.stream.domain.model.info import StreamInfo
from app.stream.domain.model.session import StreamViewerSessionInfo


@dataclass(frozen=True)
class StreamDetail:
    stream: StreamInfo
    sessions: list[StreamViewerSessionInfo]
    total_watch_minutes: int
    total_messages: int
