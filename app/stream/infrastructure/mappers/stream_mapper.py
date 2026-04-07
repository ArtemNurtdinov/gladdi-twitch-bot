from datetime import UTC, datetime

from app.stream.domain.model.info import StreamInfo
from app.stream.infrastructure.db.stream import Stream


def normalize_datetime(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def map_stream_row(row: Stream) -> StreamInfo:
    return StreamInfo(
        id=row.id,
        channel_name=row.channel_name,
        started_at=normalize_datetime(row.started_at),
        ended_at=normalize_datetime(row.ended_at),
        game_name=row.game_name,
        title=row.title,
        is_active=row.is_active,
        max_concurrent_viewers=row.max_concurrent_viewers,
        total_viewers=row.total_viewers,
        created_at=normalize_datetime(row.created_at),
        updated_at=normalize_datetime(row.updated_at),
    )
