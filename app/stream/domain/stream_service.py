from datetime import datetime

from app.stream.domain.models import StreamDetail, StreamInfo
from app.stream.domain.repo import StreamRepository


class StreamService:
    def __init__(self, repo: StreamRepository):
        self._repo = repo

    def end_stream(self, active_stream_id: int, finish_time: datetime):
        self._repo.end_stream(active_stream_id, finish_time)

    def update_stream_total_viewers(self, stream_id: int, total_viewers: int):
        self._repo.update_stream_total_viewers(stream_id, total_viewers)

    def get_active_stream(self, channel_name: str) -> StreamInfo | None:
        return self._repo.get_active_stream(channel_name)

    def update_stream_metadata(self, stream_id: int, game_name: str = None, title: str = None):
        self._repo.update_stream_metadata(stream_id, game_name, title)

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int):
        self._repo.update_max_concurrent_viewers_count(active_stream_id, viewers_count)

    def get_streams(
        self, skip: int, limit: int, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> tuple[list[StreamInfo], int]:
        return self._repo.list_streams(skip, limit, date_from, date_to)

    def get_stream_detail(self, stream_id: int) -> StreamDetail | None:
        result = self._repo.get_stream_with_sessions(stream_id)
        if not result:
            return None
        stream_info, sessions = result
        return StreamDetail(stream=stream_info, sessions=sessions)
