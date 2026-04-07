from datetime import datetime

from app.stream.domain.model.info import StreamInfo
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
