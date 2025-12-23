from datetime import datetime
from typing import Optional, Protocol

from app.stream.domain.models import StreamInfo, StreamViewerSessionInfo


class StreamRepository(Protocol):

    def start_new_stream(self, channel_name: str, started_at: datetime, game_name: str | None, title: str | None) -> None:
        ...

    def get_active_stream(self, channel_name: str) -> Optional[StreamInfo]:
        ...

    def end_stream(self, active_stream_id: int, finish_time: datetime) -> None:
        ...

    def update_stream_total_viewers(self, stream_id: int, total_viewers: int) -> None:
        ...

    def update_stream_metadata(self, stream_id: int, game_name: str | None, title: str | None) -> None:
        ...

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int) -> None:
        ...

    def list_streams(self, skip: int, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> tuple[
        list[StreamInfo], int]:
        ...

    def get_stream_with_sessions(self, stream_id: int) -> Optional[tuple[StreamInfo, list[StreamViewerSessionInfo]]]:
        ...
