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
    FollowersListResponse,
)

router = APIRouter(prefix="/followers", tags=["Followers"])


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
    return FollowerDetailResponse(
        **FollowerResponse.model_validate(result.follower, from_attributes=True).model_dump(), balance=result.balance.balance
    )
