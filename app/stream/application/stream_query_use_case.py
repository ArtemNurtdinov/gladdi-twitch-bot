from datetime import datetime

from app.stream.domain.models import StreamDetail, StreamInfo
from app.stream.domain.repo import StreamRepository


class StreamQueryUseCase:
    def __init__(self, repo: StreamRepository):
        self._repo = repo

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
