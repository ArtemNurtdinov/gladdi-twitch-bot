from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.follow.application.followers_query_use_cases import (
    GetFollowerDetailUseCase,
    ListActiveFollowersUseCase,
    ListUnfollowedFollowersUseCase,
)
from app.follow.bootstrap import (
    get_follower_detail_use_case,
    get_list_active_followers_use_case,
    get_list_unfollowed_followers_use_case,
)
from app.follow.presentation.followers_schemas import (
    FollowerDetailResponse,
    FollowerResponse,
    FollowerSessionItem,
    FollowerSessionStreamInfo,
    FollowersListResponse,
)

router = APIRouter()


@router.get("", response_model=FollowersListResponse, summary="Текущие подписчики (активные)")
async def get_active_followers(
    channel_name: str,
    use_case: ListActiveFollowersUseCase = Depends(get_list_active_followers_use_case),
):
    followers = use_case.handle(channel_name)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/unfollowed", response_model=FollowersListResponse, summary="Отписавшиеся с даты")
async def get_unfollowed_followers(
    channel_name: str,
    since: datetime = Query(..., description="Дата/время, от которой считать отписавшихся (unfollowed_at >=)"),
    until: datetime | None = Query(None, description="Опционально: верхняя граница (unfollowed_at <=)"),
    use_case: ListUnfollowedFollowersUseCase = Depends(get_list_unfollowed_followers_use_case),
):
    followers = use_case.handle(channel_name, since, until)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/{channel_name}/{user_name}", response_model=FollowerDetailResponse, summary="Детали подписчика")
async def get_follower_detail(
    channel_name: str,
    user_name: str,
    use_case: GetFollowerDetailUseCase = Depends(get_follower_detail_use_case),
):
    result = use_case.handle(channel_name, user_name)
    if not result:
        raise HTTPException(status_code=404, detail="Подписчик не найден")

    def to_session_item(s):
        stream_info = None
        if s.stream:
            stream_info = FollowerSessionStreamInfo(
                id=s.stream.id,
                title=s.stream.title,
                game_name=s.stream.game_name,
                started_at=s.stream.started_at,
                ended_at=s.stream.ended_at,
            )
        return FollowerSessionItem(
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
    return FollowerDetailResponse(
        **FollowerResponse.model_validate(result.follower, from_attributes=True).model_dump(),
        balance=result.balance.balance,
        sessions=sessions_response,
    )
