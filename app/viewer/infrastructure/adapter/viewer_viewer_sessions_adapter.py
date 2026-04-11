from app.viewer.application.model.viewer_detail_models import ViewerSessionDetail, ViewerStreamBrief
from app.viewer.application.port.viewer_detail_sessions_port import ViewerDetailSessionsPort
from app.viewer.session.application.model.viewer_session import ViewerSessionDTO
from app.viewer.session.application.usecase.get_user_sessions_use_case import GetUserSessionsUseCase


class ViewerViewerSessionsAdapter(ViewerDetailSessionsPort):
    def __init__(self, viewer_query_service: GetUserSessionsUseCase):
        self._viewer_service = viewer_query_service

    def get_user_sessions(self, channel_name: str, user_name: str) -> list[ViewerSessionDetail]:
        user_sessions = self._viewer_service.get_user_sessions(channel_name, user_name)
        return [self._to_session_detail(session) for session in user_sessions]

    def _to_session_detail(self, session: ViewerSessionDTO) -> ViewerSessionDetail:
        stream = None
        if session.stream:
            stream = ViewerStreamBrief(
                id=session.stream.id,
                title=session.stream.title,
                game_name=session.stream.game_name,
                started_at=session.stream.started_at,
                ended_at=session.stream.ended_at,
            )
        return ViewerSessionDetail(
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
            stream=stream,
        )
