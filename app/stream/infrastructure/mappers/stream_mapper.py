from app.stream.domain.models import StreamInfo
from app.stream.infrastructure.db.stream import Stream


def map_stream_row(row: Stream) -> StreamInfo:
    return StreamInfo(
        id=row.id,
        channel_name=row.channel_name,
        started_at=row.started_at,
        ended_at=row.ended_at,
        game_name=row.game_name,
        title=row.title,
        is_active=row.is_active,
        max_concurrent_viewers=row.max_concurrent_viewers,
        total_viewers=row.total_viewers,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
