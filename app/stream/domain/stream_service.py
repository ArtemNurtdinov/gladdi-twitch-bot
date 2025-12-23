import logging
from datetime import datetime
from typing import Optional

from app.stream.domain.models import StreamInfo, StreamDetail
from app.stream.domain.repo import StreamRepository

logger = logging.getLogger(__name__)


class StreamService:

    def __init__(self, repo: StreamRepository):
        self._repo = repo

    def end_stream(self, active_stream_id: int, finish_time: datetime):
        self._repo.end_stream(active_stream_id, finish_time)

    def update_stream_total_viewers(self, stream_id: int, total_viewers: int):
        self._repo.update_stream_total_viewers(stream_id, total_viewers)

    def get_active_stream(self, channel_name: str) -> Optional[StreamInfo]:
        return self._repo.get_active_stream(channel_name)

    def update_stream_metadata(self, stream_id: int, game_name: str = None, title: str = None):
        self._repo.update_stream_metadata(stream_id, game_name, title)

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int):
        self._repo.update_max_concurrent_viewers_count(active_stream_id, viewers_count)

    def get_streams(self, skip: int, limit: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> tuple[list[StreamInfo], int]:
        return self._repo.list_streams(skip, limit, date_from, date_to)

    def get_stream_detail(self, stream_id: int) -> Optional[StreamDetail]:
        result = self._repo.get_stream_with_sessions(stream_id)
        if not result:
            return None
        stream_info, sessions = result
        return StreamDetail(stream=stream_info, sessions=sessions)
