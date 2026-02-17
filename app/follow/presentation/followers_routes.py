from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.follow.application.followers_query_use_cases import (
    ListActiveFollowersUseCase,
    ListUnfollowedFollowersUseCase,
)
from app.follow.bootstrap import (
    get_list_active_followers_use_case,
    get_list_unfollowed_followers_use_case,
)
from app.follow.presentation.followers_schemas import (
    FollowerResponse,
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
