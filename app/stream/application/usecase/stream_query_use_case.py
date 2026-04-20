from datetime import UTC, datetime

from app.chat.domain.repo import ChatRepository
from app.stream.domain.model.detail import StreamDetail
from app.stream.domain.model.info import StreamInfo
from app.stream.domain.repo import StreamRepository


class StreamQueryUseCase:
    def __init__(self, repo: StreamRepository, chat_repository: ChatRepository):
        self._repo = repo
        self._chat_repository = chat_repository

    def get_streams(self, skip: int, limit: int) -> tuple[list[StreamInfo], int]:
        return self._repo.list_streams(skip, limit)

    def get_stream_detail(self, stream_id: int) -> StreamDetail | None:
        result = self._repo.get_stream_with_sessions(stream_id)
        if not result:
            return None
        stream_info, sessions = result
        total_watch_minutes = sum(s.total_minutes for s in sessions)
        start = stream_info.started_at
        end = stream_info.ended_at if stream_info.ended_at is not None else datetime.now(UTC)
        total_messages = self._chat_repository.count_between(stream_info.channel_name, start, end)
        return StreamDetail(stream=stream_info, sessions=sessions, total_watch_minutes=total_watch_minutes, total_messages=total_messages)
