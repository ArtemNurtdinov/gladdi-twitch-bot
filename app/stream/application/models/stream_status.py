from dataclasses import dataclass

from app.stream.application.models.stream_info import StreamInfoDTO


@dataclass(frozen=True)
class StreamStatusDTO:
    is_online: bool
    stream_data: StreamInfoDTO | None = None
