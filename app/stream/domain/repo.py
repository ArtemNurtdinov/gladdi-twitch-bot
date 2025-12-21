from datetime import datetime
from typing import Generic, Optional, Protocol, TypeVar

from app.stream.domain.models import StreamInfo, StreamViewerSessionInfo

DB = TypeVar("DB")


class StreamRepository(Protocol, Generic[DB]):

    def start_new_stream(self, db: DB, channel_name: str, started_at: datetime, game_name: str | None, title: str | None) -> None:
        ...

    def get_active_stream(self, db: DB, channel_name: str) -> Optional[StreamInfo]:
        ...

    def end_stream(self, db: DB, active_stream_id: int, finish_time: datetime) -> None:
        ...

    def update_stream_total_viewers(self, db: DB, stream_id: int, total_viewers: int) -> None:
        ...

    def update_stream_metadata(self, db: DB, stream_id: int, game_name: str | None, title: str | None) -> None:
        ...

    def update_max_concurrent_viewers_count(self, db: DB, active_stream_id: int, viewers_count: int) -> None:
        ...

    def list_streams(self, db: DB, skip: int, limit: int, date_from: Optional[datetime], date_to: Optional[datetime]) -> tuple[list[StreamInfo], int]:
        ...

    def get_stream_with_sessions(self, db: DB, stream_id: int) -> Optional[tuple[StreamInfo, list[StreamViewerSessionInfo]]]:
        ...

