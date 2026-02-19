from datetime import datetime, timezone

from app.stream.application.stream_chat_stats_port import StreamChatStatsPort
from app.stream.domain.models import StreamDetail, StreamInfo
from app.stream.domain.repo import StreamRepository


class StreamQueryUseCase:
    def __init__(self, repo: StreamRepository, chat_stats: StreamChatStatsPort):
        self._repo = repo
        self._chat_stats = chat_stats

    def get_streams(
        self, skip: int, limit: int, date_from: datetime | None = None, date_to: datetime | None = None
    ) -> tuple[list[StreamInfo], int]:
        return self._repo.list_streams(skip, limit, date_from, date_to)

    def get_stream_detail(self, stream_id: int) -> StreamDetail | None:
        result = self._repo.get_stream_with_sessions(stream_id)
        if not result:
            return None
        stream_info, sessions = result
        total_watch_minutes = sum(s.total_minutes for s in sessions)
        start = stream_info.started_at
        end = stream_info.ended_at if stream_info.ended_at is not None else datetime.now(timezone.utc)
        total_messages = self._chat_stats.count_messages(stream_info.channel_name, start, end)
        return StreamDetail(
            stream=stream_info, sessions=sessions, total_watch_minutes=total_watch_minutes, total_messages=total_messages
        )
