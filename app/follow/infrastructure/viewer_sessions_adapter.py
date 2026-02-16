from app.follow.application.user_sessions_port import SessionDetail, StreamBrief, UserSessionsQueryPort
from app.viewer.application.viewer_query_service import ViewerQueryService


class ViewerSessionsAdapter(UserSessionsQueryPort):
    def __init__(self, viewer_query_service: ViewerQueryService):
        self._viewer_service = viewer_query_service

    def get_user_sessions(self, channel_name: str, user_name: str) -> list[SessionDetail]:
        dtos = self._viewer_service.get_user_sessions(channel_name, user_name)
        return [self._to_session_detail(d) for d in dtos]

    def _to_session_detail(self, dto) -> SessionDetail:
        stream = None
        if dto.stream:
            stream = StreamBrief(
                id=dto.stream.id,
                title=dto.stream.title,
                game_name=dto.stream.game_name,
                started_at=dto.stream.started_at,
                ended_at=dto.stream.ended_at,
            )
        return SessionDetail(
            id=dto.id,
            stream_id=dto.stream_id,
            channel_name=dto.channel_name,
            user_name=dto.user_name,
            session_start=dto.session_start,
            session_end=dto.session_end,
            total_minutes=dto.total_minutes,
            last_activity=dto.last_activity,
            is_watching=dto.is_watching,
            rewards_claimed=dto.rewards_claimed,
            last_reward_claimed=dto.last_reward_claimed,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            stream=stream,
        )
