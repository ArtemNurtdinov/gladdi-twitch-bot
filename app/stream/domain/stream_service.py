from app.stream.domain.model.info import StreamInfo
from app.stream.domain.repo import StreamRepository


class StreamService:
    def __init__(self, repo: StreamRepository):
        self._repo = repo

    def get_active_stream(self, channel_name: str) -> StreamInfo | None:
        return self._repo.get_active_stream(channel_name)

    def update_max_concurrent_viewers_count(self, active_stream_id: int, viewers_count: int):
        self._repo.update_max_concurrent_viewers_count(active_stream_id, viewers_count)
