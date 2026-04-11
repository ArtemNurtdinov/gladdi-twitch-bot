from fastapi import APIRouter, Depends

from app.viewer.application.model.viewer_detail_models import ViewerSessionDetail
from app.viewer.application.usecase.get_viewer_detail_use_case import GetViewerDetailUseCase
from app.viewer.di.composition import get_get_viewer_detail_use_case
from app.viewer.presentation.api.model.viewer_schemas import (
    ViewerDetailResponse,
    ViewerSessionItem,
    ViewerSessionStreamInfo,
)

router = APIRouter(prefix="/viewers", tags=["Viewers"])


@router.get("/{channel_name}/{user_name}", response_model=ViewerDetailResponse, summary="Детали пользователя")
async def get_viewer_detail(
    channel_name: str,
    user_name: str,
    use_case: GetViewerDetailUseCase = Depends(get_get_viewer_detail_use_case),
):
    result = use_case.handle(channel_name, user_name)
    u = result.user_info

    def to_session_item(s: ViewerSessionDetail):
        stream_info = None
        if s.stream:
            stream_info = ViewerSessionStreamInfo(
                id=s.stream.id,
                title=s.stream.title,
                game_name=s.stream.game_name,
                started_at=s.stream.started_at,
                ended_at=s.stream.ended_at,
            )
        return ViewerSessionItem(
            id=s.id,
            stream_id=s.stream_id,
            channel_name=s.channel_name,
            user_name=s.user_name,
            session_start=s.session_start,
            session_end=s.session_end,
            total_minutes=s.total_minutes,
            last_activity=s.last_activity,
            is_watching=s.is_watching,
            rewards_claimed=s.rewards_claimed,
            last_reward_claimed=s.last_reward_claimed,
            created_at=s.created_at,
            updated_at=s.updated_at,
            stream=stream_info,
        )

    sessions_response = [to_session_item(s) for s in result.sessions]
    return ViewerDetailResponse(
        channel_name=u.channel_name,
        user_name=u.user_name,
        display_name=u.display_name,
        followed_at=u.followed_at,
        first_seen_at=u.first_seen_at,
        last_seen_at=u.last_seen_at,
        unfollowed_at=u.unfollowed_at,
        is_active=u.is_active,
        created_at=u.created_at,
        updated_at=u.updated_at,
        balance=result.balance.balance,
        sessions=sessions_response,
    )
