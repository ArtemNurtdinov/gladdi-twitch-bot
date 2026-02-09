from app.stream.domain.models import StreamInfo
from app.viewer.application.dto import StreamInfoDto, ViewerSessionDto
from app.viewer.domain.models import ViewerSession
from app.viewer.domain.viewer_session_service import ViewerTimeService


class ViewerQueryService:

    def __init__(self, service: ViewerTimeService):
        self._service = service

    def _to_stream_dto(self, stream: StreamInfo | None) -> StreamInfoDto | None:
        if stream is None:
            return None
        return StreamInfoDto(
            id=stream.id,
            title=stream.title,
            game_name=stream.game_name,
            started_at=stream.started_at,
            ended_at=stream.ended_at,
        )

    def _to_session_dto(self, session: ViewerSession) -> ViewerSessionDto:
        return ViewerSessionDto(
            id=session.id,
            stream_id=session.stream_id,
            channel_name=session.channel_name,
            user_name=session.user_name,
            session_start=session.session_start,
            session_end=session.session_end,
            total_minutes=session.total_minutes,
            last_activity=session.last_activity,
            is_watching=session.is_watching,
            rewards_claimed=session.rewards_claimed,
            last_reward_claimed=session.last_reward_claimed,
            created_at=session.created_at,
            updated_at=session.updated_at,
            stream=self._to_stream_dto(session.stream),
        )

    def get_user_sessions(self, channel_name: str, user_name: str) -> list[ViewerSessionDto]:
        sessions = self._service.get_user_sessions(channel_name, user_name)
        return [self._to_session_dto(session) for session in sessions]
