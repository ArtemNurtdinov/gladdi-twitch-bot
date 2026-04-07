from fastapi import APIRouter
from fastapi.params import Depends

from app.bot.presentation.api.bot_twitch_routes import get_economy_container, get_follow_container, get_viewer_container
from app.economy.di.container import EconomyContainer
from app.follow.di.container import FollowContainer
from app.viewer.application.model.viewer_detail_models import ViewerSessionDetail
from app.viewer.di.container import ViewerContainer
from app.viewer.presentation.api.model.viewer_schemas import (
    ViewerDetailResponse,
    ViewerSessionItem,
    ViewerSessionStreamInfo,
)
from core.db import db_ro_session

router = APIRouter(prefix="/viewers", tags=["Viewers"])


@router.get("/{channel_name}/{user_name}", response_model=ViewerDetailResponse, summary="Детали пользователя")
async def get_viewer_detail(
    channel_name: str,
    user_name: str,
    economy_container: EconomyContainer = Depends(get_economy_container),
    follow_container: FollowContainer = Depends(get_follow_container),
    viewer_container: ViewerContainer = Depends(get_viewer_container),
):
    with db_ro_session() as session:
        economy_policy = economy_container.economy_policy(session)
        followers_repo = follow_container.followers_repository(session)
        get_viewer_detail_use_case = viewer_container.get_viewer_detail_use_case(followers_repo, economy_policy, session)
        result = get_viewer_detail_use_case.handle(channel_name, user_name)

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
        channel_name=result.user_info.channel_name,
        user_name=result.user_info.user_name,
        display_name=result.user_info.display_name,
        followed_at=result.user_info.followed_at,
        first_seen_at=result.user_info.first_seen_at,
        last_seen_at=result.user_info.last_seen_at,
        unfollowed_at=result.user_info.unfollowed_at,
        is_active=result.user_info.is_active,
        created_at=result.user_info.created_at,
        updated_at=result.user_info.updated_at,
        balance=result.balance.balance,
        sessions=sessions_response,
    )
