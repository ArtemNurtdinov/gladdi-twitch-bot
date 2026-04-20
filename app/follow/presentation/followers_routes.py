from fastapi import APIRouter

from app.follow.di.container import FollowContainer
from app.follow.presentation.followers_schemas import (
    FollowerResponse,
    FollowersListResponse,
)
from core.db import db_ro_session

router = APIRouter()


@router.get("", response_model=FollowersListResponse, summary="Текущие подписчики (активные)")
async def get_active_followers(channel_name: str):
    follow_container = FollowContainer()
    with db_ro_session() as session:
        active_followers_use_case = follow_container.get_active_followers_use_case(session)
        followers = active_followers_use_case.handle(channel_name)

    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/unfollowed", response_model=FollowersListResponse, summary="Отписавшиеся с даты")
async def get_unfollowed_followers(
    channel_name: str,
):
    follow_container = FollowContainer()
    with db_ro_session() as session:
        unfollowed_use_case = follow_container.get_unfollowed_use_case(session)
        followers = unfollowed_use_case.handle(channel_name)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])
