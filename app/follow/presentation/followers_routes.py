from datetime import datetime

from fastapi import APIRouter, Query

from app.follow.di.composition import get_active_followers_use_case, get_unfollowed_use_case
from app.follow.presentation.followers_schemas import (
    FollowerResponse,
    FollowersListResponse,
)
from core.db import db_ro_session

router = APIRouter()


@router.get("", response_model=FollowersListResponse, summary="Текущие подписчики (активные)")
async def get_active_followers(channel_name: str):
    with db_ro_session() as session:
        active_followers_use_case = get_active_followers_use_case(session)
        followers = active_followers_use_case.handle(channel_name)

    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/unfollowed", response_model=FollowersListResponse, summary="Отписавшиеся с даты")
async def get_unfollowed_followers(
    channel_name: str,
    since: datetime = Query(..., description="Дата/время, от которой считать отписавшихся (unfollowed_at >=)"),
    until: datetime | None = Query(None, description="Опционально: верхняя граница (unfollowed_at <=)"),
):
    with db_ro_session() as session:
        unfollowed_use_case = get_unfollowed_use_case(session)
        followers = unfollowed_use_case.handle(channel_name, since, until)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])
