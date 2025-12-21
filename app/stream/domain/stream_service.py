import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.stream.domain.models import StreamInfo, StreamDetail
from app.stream.domain.repo import StreamRepository

logger = logging.getLogger(__name__)


class StreamService:

    def __init__(self, repo: StreamRepository[Session]):
        self._repo = repo

    def start_new_stream(self, db: Session, channel_name: str, started_at: datetime, game_name: str | None = None, title: str | None = None) -> None:
        active_stream = self._repo.get_active_stream(db, channel_name)
        if active_stream:
            logger.warning(f"Попытка начать стрим, но активный стрим уже существует: {active_stream.id}")
            return

        self._repo.start_new_stream(db, channel_name, started_at, game_name, title)

    def end_stream(self, db: Session, active_stream_id: int, finish_time: datetime):
        self._repo.end_stream(db, active_stream_id, finish_time)

    def update_stream_total_viewers(self, db: Session, stream_id: int, total_viewers: int):
        self._repo.update_stream_total_viewers(db, stream_id, total_viewers)

    def get_active_stream(self, db: Session, channel_name: str) -> Optional[StreamInfo]:
        return self._repo.get_active_stream(db, channel_name)

    def update_stream_metadata(self, db: Session, stream_id: int, game_name: str = None, title: str = None):
        self._repo.update_stream_metadata(db, stream_id, game_name, title)

    def update_max_concurrent_viewers_count(self, db: Session, active_stream_id: int, viewers_count: int):
        self._repo.update_max_concurrent_viewers_count(db, active_stream_id, viewers_count)

    def get_streams(self, db: Session, skip: int, limit: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> tuple[list[StreamInfo], int]:
        return self._repo.list_streams(db, skip, limit, date_from, date_to)

    def get_stream_detail(self, db: Session, stream_id: int) -> Optional[StreamDetail]:
        result = self._repo.get_stream_with_sessions(db, stream_id)
        if not result:
            return None
        stream_info, sessions = result
        return StreamDetail(stream=stream_info, sessions=sessions)
